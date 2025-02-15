from typing import List, Dict
import openai
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import pinecone
from ..config import Config

class ChatbotService:
    def __init__(self):
        """Khởi tạo ChatbotService với các thành phần cần thiết"""
        # Khởi tạo OpenAI
        openai.api_key = Config.OPENAI_API_KEY
        
        # Khởi tạo Pinecone
        pinecone.init(
            api_key=Config.PINECONE_API_KEY,
            environment=Config.PINECONE_ENVIRONMENT
        )
        
        # Khởi tạo embedding model
        self.embeddings = OpenAIEmbeddings()
        
        # Khởi tạo vector store
        self.vectorstore = Pinecone.from_existing_index(
            index_name=Config.PINECONE_INDEX,
            embedding=self.embeddings
        )
        
        # Khởi tạo chat model
        self.llm = ChatOpenAI(temperature=0.7)
        
        # Khởi tạo memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Khởi tạo conversation chain
        self.qa = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(),
            memory=self.memory,
            verbose=True
        )

    def get_response(self, user_message: str) -> str:
        """
        Xử lý tin nhắn của người dùng và trả về câu trả lời
        
        Args:
            user_message: Tin nhắn của người dùng
            
        Returns:
            str: Câu trả lời của chatbot
        """
        try:
            # Thêm system prompt để định hướng chatbot
            system_prompt = """Bạn là trợ lý AI của nhà hàng. Nhiệm vụ của bạn là:
            1. Trả lời các câu hỏi về menu, món ăn
            2. Hỗ trợ đặt bàn
            3. Cung cấp thông tin về lịch hoạt động
            4. Tư vấn về các combo, khuyến mãi
            5. Giải đáp các thắc mắc khác về nhà hàng
            
            Hãy trả lời một cách thân thiện, chuyên nghiệp và chính xác."""
            
            # Tạo prompt đầy đủ
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"
            
            # Lấy câu trả lời từ conversation chain
            response = self.qa({"question": full_prompt})
            
            return response['answer']
            
        except Exception as e:
            return f"Xin lỗi, có lỗi xảy ra: {str(e)}"

    def train_knowledge(self, documents: List[Dict[str, str]]):
        """
        Cập nhật knowledge base với dữ liệu mới
        
        Args:
            documents: Danh sách các document cần thêm vào knowledge base
            Format: [{"text": "nội dung", "metadata": {...}}]
        """
        try:
            # Tạo embeddings và lưu vào Pinecone
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            self.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Lỗi khi training: {str(e)}")
            return False
