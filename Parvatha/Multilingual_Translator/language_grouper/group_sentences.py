import spacy 
from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer, util
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from langdetect import detect
import torch
import spacy
import numpy as np
from langdetect import detect
from typing import List, Union
from sentence_transformers import SentenceTransformer, util

nlp = spacy.blank("xx")  # "xx" is a multilingual model for sentence segmentation
nlp.add_pipe("sentencizer")
model = SentenceTransformer('sentence-transformers/LaBSE')

class Reader:
    def __init__(self, nlp: spacy.language.Language, model: SentenceTransformer) -> None:
        """
        Initialize the Reader class.
        Args:
            nlp: A SpaCy pipeline object.
            model: A SentenceTransformer model.
        Example: 
        ```python
        nlp = spacy.blank("xx")
        nlp.add_pipe("sentencizer")
        model = SentenceTransformer('sentence-transformers/LaBSE')
        ```
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.nlp = nlp 
        self.model = model.to(self.device)

    @staticmethod
    def split_into_sentences(nlp: spacy.language.Language, document: str) -> Union[List[str], List[str]]:
        """
        Process a document using SpaCy's multilingual pipeline and detect the language of each sentence.
        Args:
            nlp: A SpaCy pipeline object
            document (str): The document to process.
        Returns:
            tuple: (list of sentences, list of corresponding detected languages)
        """
        # Process the document to split sentences
        doc = nlp(document)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        languages = []
        for sentence in sentences:
            try:
                lang = detect(sentence)
            except:
                lang = None
            languages.append(lang)
        return sentences, languages
    
    @staticmethod
    def get_similarity_matrix(sentences: List[str], model: SentenceTransformer, 
                              device: torch.device, verbose: bool = True) -> torch.Tensor:
        """ 
        Get similarity matrix for a list of sentences.
        Args:
            sentences: A list of strings.
            model: A SentenceTransformer model.
            device: A torch.device.
            verbose: A boolean. if true, shows the progress of calculating the similarity matrix.
        Returns:
            A torch.Tensor containing the similarity matrix.
        """
        # Encode sentences as tensors on the given device
        embeddings = model.encode(sentences, device=device.type, show_progress_bar=verbose, convert_to_tensor=True)
        # Compute cosine similarity
        similarity_matrix = util.cos_sim(embeddings, embeddings)
        return similarity_matrix
    
    @staticmethod
    def get_similar_sentences(similarity_matrix: np.ndarray, sentences: List[str], languages: List[str],
                              threshold: float = 0.8) -> dict:
        """ 
        Get similar sentences from a similarity matrix.
        Args:
            similarity_matrix: A numpy array containing the cosine similarity matrix.
            sentences: A list of sentences.
            languages: A list of languages corresponding to the sentences.
            threshold: A float representing the similarity threshold. Default is 0.8.
        Returns:
            A dictionary containing [source sentence, target sentence, source language, target language, similarity score].
        """
        sentence1_indices, sentence2_indices = np.where(similarity_matrix > threshold)
        data = {
            "source": [],
            "target": [],
            "source_lang": [],
            "target_lang": [],
            "similarity": []
        }
        
        for sentence1_idx, sentence2_idx in zip(sentence1_indices, sentence2_indices):
            if sentence1_idx != sentence2_idx:  # avoid comparing the same sentence
                data["source"].append(sentences[sentence1_idx])
                data["target"].append(sentences[sentence2_idx])
                data["source_lang"].append(languages[sentence1_idx])
                data["target_lang"].append(languages[sentence2_idx])
                data["similarity"].append(similarity_matrix[sentence1_idx, sentence2_idx])
        
        return data

    def run_pipeline(self, document: str, similarity_threshold: float = 0.8) -> Union[dict, np.ndarray]:
        """ 
        Run the pipeline to group similar sentences in a document.
        Args:
            document: A string containing the document with various sentences in different languages.
            similarity_threshold: A float representing the similarity threshold to consider two sentences similar.
                                  Default is 0.8.
        Returns:
            similar_sentences: A dictionary containing [source sentence, target sentence, source language, target language, similarity score].
            similarity_matrix: A numpy array containing the similarity matrix.
        """
        sentences, languages = self.split_into_sentences(self.nlp, document)
        if not sentences:
            return {}, np.array([])

        similarity_matrix = self.get_similarity_matrix(sentences, self.model, 
                                                       device=self.device, verbose=True)
        similar_sentences = self.get_similar_sentences(similarity_matrix.cpu().numpy(), 
                                                       sentences, languages,
                                                       threshold=similarity_threshold)
        return similar_sentences, similarity_matrix.cpu().numpy()


if __name__ == "__main__":

    # Example multilingual document
    document = """
    The quick brown fox jumps over the lazy dog. El rápido zorro marrón salta sobre el perro perezoso. Le rapide renard brun saute par-dessus le chien paresseux. Der schnelle braune Fuchs springt über den faulen Hund. Il rapido volpe marrone salta sopra il cane pigro. O rápido raposo marrom pula sobre o cachorro preguiçoso. Быстрая коричневая лиса прыгает через ленивую собаку. 快速的棕色狐狸跳过了懒狗。速い茶色のキツネが怠惰な犬を飛び越えます。 तेज़ भूरी लोमड़ी आलसी कुत्ते के ऊपर कूद जाती है।  السريع الثعلب البني يقفز فوق الكلب الكسول.
    """

    reader = Reader(nlp, model)
    similar_sentences, similarity_matrix = reader.run_pipeline(document, similarity_threshold=0.8)
    
    # Convert the similar sentences to a DataFrame
    import pandas as pd
    df = pd.DataFrame(similar_sentences)
    print(df)


    sns.heatmap(similarity_matrix, annot=True, cmap="YlGnBu")
    plt.show()