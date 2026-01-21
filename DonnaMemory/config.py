import os

class Config:
    """Configuration for Donna Memory Microservice."""
    
    # Pinecone Configuration
    # In production, use os.getenv("PINECONE_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_2vqLqd_GwCV25x1xrWxWvNR2R7rcZkaj7u8Qhfo95cW2A7G5gsVFGK8aiCSgbCrskkNFew")
    PINECONE_ENV = "us-east-1"
    PINECONE_CLOUD = "aws"
    
    # Index Name
    INDEX_NAME = "donna-memory-v1"
    
    # Model Configuration
    EMBEDDING_MODEL = "multilingual-e5-large"  # High quality, good for mixed languages
