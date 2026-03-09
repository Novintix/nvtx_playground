from torch.utils.data import Dataset, DataLoader
from read_pdf import read_pdf_batch
import os 
from tqdm import tqdm
from group_sentences import Reader
import spacy
from sentence_transformers import SentenceTransformer

class PDFDataset(Dataset):
    """
    A custom Dataset class for handling PDF files.
    """
    def __init__(self, pdf_directory):
        """
        Initialize the dataset with the directory containing PDFs.
        Args:
            pdf_directory (str): Path to the directory containing PDF files.
        """
        self.pdf_files = [os.path.join(pdf_directory, f) for f in 
                          os.listdir(pdf_directory) if f.lower().endswith('.pdf')]

    def __len__(self):
        """
        Return the number of PDFs in the dataset.
        """
        return len(self.pdf_files)

    def __getitem__(self, idx):
        """
        Return the file path of the PDF at the given index.
        Args:
            idx (int): Index of the PDF.
        Returns:
            str: File path of the PDF.
        """
        return self.pdf_files[idx]
    

class TextDataset(Dataset):
    """
    A custom Dataset class for handling text files.
    """
    def __init__(self, text_directory):
        """
        Initialize the dataset with the directory containing text files.
        Args:
            text_directory (str): Path to the directory containing text files.
        """
        self.text_files = [os.path.join(text_directory, f) for f in 
                           os.listdir(text_directory) if f.lower().endswith('.txt')]

    def __len__(self):
        """
        Return the number of text files in the dataset.
        """
        return len(self.text_files)

    def __getitem__(self, idx):
        """
        Return the entire text content of the text file at the given index.
        Args:
            idx (int): Index of the text file.
        Returns:
            str: File path of the text file.
        """
        with open(self.text_files[idx], 'r', encoding='utf-8') as f:
            return f.read()
        


def process_pdfs_to_text(pdf_dir: str, batch_size: int, num_worker: int, 
                        output_directory: str = "output"):
    """Read the pdfs and convert them to text and save them in text files
    Args:
        pdf_dir (str): Directory containing PDF files
        batch_size (int): Batch size for processing PDFs
        num_worker (int): Number of workers for DataLoader
        output_directory (str): Directory to save the extracted text files. 
                                Defaults to "output".
    """
    os.makedirs(output_directory, exist_ok=True)
    # Initialize the dataset and DataLoader
    dataset = PDFDataset(pdf_directory=pdf_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, 
                            num_workers=num_worker, shuffle=False)

    # Process each batch of PDFs
    loop = tqdm(dataloader, desc="Processing PDF batches")
    for batch in loop:
        read_pdf_batch(batch, output_directory)
        loop.set_postfix({"Processed": len(batch)})


# def process_texts_to_df(text_dir: str, batch_size: int, num_worker: int):
#     """Read the text files and convert them to pandas DataFrame
#     Args:
#         text_dir (str): Directory containing text files
#         batch_size (int): Batch size for processing text files
#         num_worker (int): Number of workers for DataLoader
#     Returns:
#         pd.DataFrame: DataFrame containing the text content of the text files
#     """
#     # Initialize the dataset and DataLoader
#     dataset = TextDataset(text_directory=text_dir)
#     dataloader = DataLoader(dataset, batch_size=batch_size, 
#                             num_workers=num_worker, shuffle=False)

#     all_texts = []
#     # Process each batch of text files
#     loop = tqdm(dataloader, desc="Processing text batches")
#     for batch in loop:
#         all_texts.extend(batch)
#         loop.set_postfix({"Processed": len(all_texts)})

#     return pd.DataFrame({"text": all_texts})


if __name__ == "__main__":
    input_directory = "/Users/archismanchakraborti/Downloads/pdfs"  # Replace with your PDF directory
    output_directory = "output"  # Replace with your output directory

    # Parameters
    batch_size = 2
    num_workers = 0
    similarity_threshold = 0.8

    # Process PDFs to text and save to output directory
    print("Processing PDFs...\n\n")
    process_pdfs_to_text(input_directory, batch_size, num_workers, output_directory)
    print("\n\n PDFs processed successfully.")


    # # Read and group text files

    # nlp = spacy.blank("xx")  # "xx" is a multilingual model for sentence segmentation
    # nlp.add_pipe("sentencizer")
    # model = SentenceTransformer('sentence-transformers/LaBSE')

    # reader = Reader(nlp, model)