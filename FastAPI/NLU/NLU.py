import onnxruntime as ort
import numpy as np
from transformers import BertTokenizer
import json
import time

class ONNXBertNERPredictor:
    def __init__(self, model_metadata_path: str, onnx_model_path: str, max_len: int = 128, device: str = 'cpu'):
        # Load metadata from model_metadata.json
        with open(model_metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        # Extract necessary components from metadata
        self.id2label = {int(k): v for k, v in self.metadata['id2label'].items()}  # Convert keys to integers
        self.label2id = self.metadata['label2id']
        self.num_labels = self.metadata['num_labels']
        self.pretrained_model = self.metadata['pretrained_model']

        # Load the tokenizer based on the pretrained model from metadata
        self.tokenizer = BertTokenizer.from_pretrained(self.pretrained_model)
        
        # Load the ONNX model using ONNX Runtime
        self.ort_session = ort.InferenceSession(onnx_model_path)
        
        # Store other attributes
        self.max_len = max_len
        self.device = device
    
    def predict(self, sentence: str) -> dict:
        # Record start time
        start_time = time.time()
        
        # Tokenize the input sentence
        inputs = self.tokenizer(sentence, padding='max_length', truncation=True, max_length=self.max_len, return_tensors="np")
        
        # ONNX input names should match the names used in export step
        input_ids = inputs["input_ids"].astype(np.int64)
        attention_mask = inputs["attention_mask"].astype(np.int64)

        # Run the ONNX model and get the output
        ort_inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }

        ort_outs = self.ort_session.run(None, ort_inputs)
        logits = ort_outs[0]

        # Get predictions and convert them into human-readable form
        active_logits = logits.reshape(-1, len(self.id2label))
        top_predictions = np.argmax(active_logits, axis=1)

        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        
        # Prepare final output with tokens and labels
        predictions = []
        for token, pred_idx in zip(tokens, top_predictions):
            if token not in ['[CLS]', '[SEP]', '[PAD]']:
                predictions.append((token, self.id2label[pred_idx]))

        # Record end time and calculate elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Return the sentence, the response, and the elapsed time
        return {
            "request": sentence,
            "response": predictions,
            "prediction_time_in_seconds": elapsed_time
        }

# Example usage:
if __name__ == "__main__":
    # Initialize the predictor with metadata and model paths
    model_metadata_path = 'model_metadata.json'
    onnx_model_path = 'model.onnx'
    
    predictor = ONNXBertNERPredictor(model_metadata_path, onnx_model_path)

    # Example input sentence (in Persian)
    sentence = "هی ربات من پسرم سرماخورده و براش دنبال فوق تخصص داخلی میگردم. برا پسرم یکی و توی زینبیه علی آباد پیدا کن غیر حضوری"
    sentence = "ربات میشه واسه شوهرم یک دکتر عمومی توی خرم آباد محله تجریش پیدا کنی میخوام خیلی زود و به صورت غیر حضوری برم و دکتر مهربون و خوش اخلاق باشه برای یکشنبه"
    sentence = "سلام برای بیماری قند خون پدرم نیاز به یک فوق تخصص داخلی دارم برای شنبه غیر حضوری در فدک اصفهان ."

    # Predict using the ONNX model
    final_output = predictor.predict(sentence)

    # Print the result in the desired format
    print(final_output)

