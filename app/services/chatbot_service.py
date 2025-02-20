from typing import List, Dict
import os
import threading
from ..services.text_to_speech_service import TextToSpeechService
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from ..config import Config

class ChatbotService:
    def __init__(self):
        """Initialize ChatbotService with required components"""
        self.tts_service = TextToSpeechService()
        # Initialize OpenAI
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model_name=Config.OPENAI_MODEL,
            temperature=0.7
        )
        
        # Use HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Create vector store directory if not exists
        os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)
        
        # Initialize or load vector store
        try:
            self.vectorstore = FAISS.load_local(
                folder_path=Config.VECTOR_STORE_PATH,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            print(f"Cannot load vector store, creating new one: {str(e)}")
            # Initialize new vector store with data from knowledge dir
            texts = self._load_knowledge_texts()
            self.vectorstore = FAISS.from_texts(
                texts if texts else ["Welcome to our restaurant"],
                self.embeddings
            )
            # Save vector store
            self.vectorstore.save_local(Config.VECTOR_STORE_PATH)
        
        # Initialize conversation chain
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(),
            memory=self.memory,
            verbose=True
        )

    def _load_knowledge_texts(self) -> List[str]:
        """Load texts from knowledge directory"""
        texts = []
        knowledge_dir = Config.KNOWLEDGE_DIR
        if os.path.exists(knowledge_dir):
            for filename in os.listdir(knowledge_dir):
                if filename.endswith('.txt'):
                    with open(os.path.join(knowledge_dir, filename), 'r', encoding='utf-8') as f:
                        texts.append(f.read())
        return texts

    def get_response(self, user_message: str, use_tts: bool = False):
        """
        Process user message and return response

        Args:
            user_message: Message from user

        Returns:
            str: Chatbot response
        """
        try:
            # Add system prompt inside conversation memory
            self.memory.save_context(
                {"input": "System Prompt"},
                {"output": """You are an AI assistant for the restaurant. Your tasks are:
                1. Answer questions about the menu and dishes
                2. Help with reservations
                3. Provide information about operating hours
                4. Advise about promotions and special offers
                5. Answer other questions about the restaurant

                Please be friendly, professional, and accurate."""}
            )
            response_text = self.chain({"question": user_message})['answer']
            audio_url = None

            if use_tts:
                # Run TTS in a background thread
                def generate_tts():
                    self.tts_service.text_to_speech(response_text)

                threading.Thread(target=generate_tts).start()

                # Return audio URL immediately without waiting
                audio_url = "/speak"

            return {"text": response_text, "audio_url": audio_url}

        except Exception as e:
            return {"text": f"Sorry, an error occurred: {str(e)}", "audio_url": None}

    def train_knowledge(self, documents: List[Dict[str, str]]):
        """
        Update knowledge base with new data
        
        Args:
            documents: List of documents to add to knowledge base
            Format: [{"text": "content", "metadata": {...}}]
        """
        try:
            texts = [doc["text"] for doc in documents]
            
            # Add texts to vector store
            self.vectorstore.add_texts(texts)
            
            # Save vector store
            self.vectorstore.save_local(Config.VECTOR_STORE_PATH)
            
            return True
        except Exception as e:
            print(f"Error during training: {str(e)}")
            return False
