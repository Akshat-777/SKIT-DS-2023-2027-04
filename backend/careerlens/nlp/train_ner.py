import os
import torch
import numpy as np
from typing import Dict, Any, List, Tuple
import evaluate
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
    EarlyStoppingCallback
)
from careerlens.nlp.dataset_prep import (
    LABELS, LABEL2ID, ID2LABEL, prepare_hf_dataset, weak_label_resume
)

# Custom Trainer to handle class weighting for imbalanced NER tokens (O class dominance)
class WeightedLossTrainer(Trainer):
    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if class_weights is not None:
            self.class_weights = torch.tensor(class_weights, dtype=torch.float32)
        else:
            self.class_weights = None

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        
        if self.class_weights is not None:
            weight = self.class_weights.to(logits.device)
            loss_fct = torch.nn.CrossEntropyLoss(weight=weight, ignore_index=-100)
        else:
            loss_fct = torch.nn.CrossEntropyLoss(ignore_index=-100)
            
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(p):
    """Compute seqeval precision, recall, F1 per entity and overall."""
    seqeval = evaluate.load("seqeval")
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [LABELS[p_i] for (p_i, l_i) in zip(prediction, label) if l_i != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [LABELS[l_i] for (p_i, l_i) in zip(prediction, label) if l_i != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = seqeval.compute(predictions=true_predictions, references=true_labels)
    
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"]
    }


def analyze_errors_and_confusion(predictions: List[List[str]], references: List[List[str]]) -> Dict[str, Any]:
    """
    Error analysis template: identifies entity misclassifications and confusion across classes.
    """
    confusion = {}
    error_samples = []

    for pred_seq, ref_seq in zip(predictions, references):
        for p_tag, r_tag in zip(pred_seq, ref_seq):
            if r_tag not in confusion:
                confusion[r_tag] = {}
            confusion[r_tag][p_tag] = confusion[r_tag].get(p_tag, 0) + 1
            
            if p_tag != r_tag and r_tag != "O":
                error_samples.append({
                    "expected": r_tag,
                    "predicted": p_tag
                })

    return {
        "confusion_matrix": confusion,
        "total_errors": len(error_samples),
        "error_samples": error_samples[:20]  # Sample first 20 errors
    }


def train_ner_model(
    sample_resumes: List[str] = None,
    output_dir: str = "./ner_model_output",
    model_name: str = "distilbert-base-uncased",
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 3e-5
) -> Tuple[Any, Any]:
    """
    Main training function for Resume NER token classification model.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Synthetic / Bootstrapped Dataset if none supplied
    if sample_resumes is None:
        sample_resumes = [
            "Aishani Billore\nEmail: aishani@example.com\nPhone: +91 9876543210\nEducation: B.Tech in Data Science, SKIT Jaipur, Graduated 2024.\nExperience: Software Engineer at Google (2024-Present).\nSkills: Python, React, FastAPI, Docker, PyTorch, SQL.",
            "Akshat Agarwal\nEmail: akshat@skit.ac.in\nPhone: 9988776655\nEducation: B.E. Computer Science, RTU, 2023.\nExperience: Lead Developer at TechCorp (2022-2024).\nSkills: Node.js, Express, PostgreSQL, Microservices, AWS, C++.",
            "Aryan Rathore\nEmail: aryan@ml.io\nPhone: +1 555-0199\nEducation: M.Tech Artificial Intelligence, IIT Bombay, 2022.\nExperience: Data Scientist at Analytics Inc (2022-2025).\nSkills: LightGBM, Scikit-learn, Transformers, NLP, Python, Machine Learning."
        ] * 10  # Duplicate to create mock batch

    annotated_data = [weak_label_resume(text, f"res_{i}") for i, text in enumerate(sample_resumes)]
    
    # 2. Tokenizer & Dataset Preparation
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    dataset_dict = prepare_hf_dataset(annotated_data, tokenizer_name=model_name)

    # 3. Model Initialization
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )

    # 4. Class Weights (downweight "O" tag to prevent majority class imbalance)
    class_weights = [1.0] * len(LABELS)
    class_weights[LABEL2ID["O"]] = 0.2  # Lower loss weight for "O" tag

    # 5. Device detection (CPU vs GPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[CareerLens NER Training] Using device: {device}")

    # 6. Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=epochs,
        weight_decay=0.01,
        logging_dir=os.path.join(output_dir, "logs"),
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        no_cuda=(device == "cpu"),
        save_total_limit=2
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)

    # 7. Trainer Setup
    trainer = WeightedLossTrainer(
        class_weights=class_weights,
        model=model,
        args=training_args,
        train_dataset=dataset_dict["train"],
        eval_dataset=dataset_dict["validation"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    # 8. Train Model
    trainer.train()

    # 9. Save Final Model & Tokenizer
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"[CareerLens NER Training] Model successfully saved to {output_dir}")
    return model, tokenizer


if __name__ == "__main__":
    train_ner_model()
