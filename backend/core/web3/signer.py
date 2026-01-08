"""
Web3 签名服务

为 SparkKnowledgeNFT 合约提供铸造签名
防止用户伪造光源值
"""

import os
from typing import Optional, Dict, Any
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import json

# 配置
SIGNER_PRIVATE_KEY = os.getenv("NFT_SIGNER_PRIVATE_KEY", "")
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/demo")
CONTRACT_ADDRESS = os.getenv("SPARK_NFT_CONTRACT", "")


class SparkNFTSigner:
    """
    光源 NFT 签名服务
    
    用于在用户铸造 NFT 时生成可信签名
    防止用户伪造光源值数据
    """
    
    def __init__(self, private_key: str = None):
        self.private_key = private_key or SIGNER_PRIVATE_KEY
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            self.signer_address = self.account.address
        else:
            self.account = None
            self.signer_address = None
    
    def is_configured(self) -> bool:
        """检查是否已配置私钥"""
        return self.account is not None
    
    def get_signer_address(self) -> Optional[str]:
        """获取签名者地址"""
        return self.signer_address
    
    def sign_mint_request(
        self,
        user_address: str,
        conversation_id: str,
        rag_id: str,
        spark_value: int,
        base_score: int,
        citation_score: int,
        activation_score: int,
        behavior_score: int
    ) -> Optional[Dict[str, Any]]:
        """
        签名铸造请求
        
        Args:
            user_address: 用户钱包地址
            conversation_id: 对话 ID
            rag_id: RAG ID
            spark_value: 光源值 (0-100)
            base_score: 基础分
            citation_score: 引用分
            activation_score: 激活分
            behavior_score: 行为分
        
        Returns:
            签名数据，包含 signature 和 message_hash
        """
        if not self.is_configured():
            return None
        
        # 验证光源值
        if spark_value < 70:
            return {"error": "光源值不足 70，无法铸造 NFT"}
        
        # 构建消息哈希（与合约中一致）
        message_hash = Web3.solidity_keccak(
            ['address', 'string', 'string', 'uint256', 'uint256', 'uint256', 'uint256', 'uint256'],
            [
                Web3.to_checksum_address(user_address),
                conversation_id,
                rag_id,
                spark_value,
                base_score,
                citation_score,
                activation_score,
                behavior_score
            ]
        )
        
        # 签名
        signable_message = encode_defunct(message_hash)
        signed = self.account.sign_message(signable_message)
        
        return {
            "success": True,
            "signature": signed.signature.hex(),
            "message_hash": message_hash.hex(),
            "signer": self.signer_address,
            "data": {
                "user_address": user_address,
                "conversation_id": conversation_id,
                "rag_id": rag_id,
                "spark_value": spark_value,
                "base_score": base_score,
                "citation_score": citation_score,
                "activation_score": activation_score,
                "behavior_score": behavior_score
            }
        }


class SparkNFTContract:
    """
    SparkKnowledgeNFT 合约交互类
    """
    
    # ABI（简化版，只包含需要的函数）
    ABI = [
        {
            "inputs": [
                {"name": "conversationId", "type": "string"},
                {"name": "ragId", "type": "string"},
                {"name": "ipfsCID", "type": "string"},
                {"name": "sparkValue", "type": "uint256"},
                {"name": "baseScore", "type": "uint256"},
                {"name": "citationScore", "type": "uint256"},
                {"name": "activationScore", "type": "uint256"},
                {"name": "behaviorScore", "type": "uint256"},
                {"name": "price", "type": "uint256"},
                {"name": "signature", "type": "bytes"}
            ],
            "name": "mintSparkNFT",
            "outputs": [{"name": "tokenId", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "getNFTInfo",
            "outputs": [
                {"name": "owner_", "type": "address"},
                {"components": [
                    {"name": "conversationId", "type": "string"},
                    {"name": "ragId", "type": "string"},
                    {"name": "ipfsCID", "type": "string"},
                    {"name": "sparkValue", "type": "uint256"},
                    {"name": "baseScore", "type": "uint256"},
                    {"name": "citationScore", "type": "uint256"},
                    {"name": "activationScore", "type": "uint256"},
                    {"name": "behaviorScore", "type": "uint256"},
                    {"name": "rarity", "type": "uint8"},
                    {"name": "creator", "type": "address"},
                    {"name": "createdAt", "type": "uint64"},
                    {"name": "isActive", "type": "bool"},
                    {"name": "price", "type": "uint256"},
                    {"name": "totalSales", "type": "uint256"},
                    {"name": "totalRevenue", "type": "uint256"}
                ], "name": "nft", "type": "tuple"},
                {"components": [
                    {"name": "amount", "type": "uint256"},
                    {"name": "stakedAt", "type": "uint256"},
                    {"name": "lockPeriod", "type": "uint256"},
                    {"name": "rewardRate", "type": "uint256"}
                ], "name": "stake", "type": "tuple"},
                {"name": "reward", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "conversationId", "type": "string"}],
            "name": "getTokenByConversation",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "conversationId", "type": "string"}],
            "name": "isConversationMinted",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "user", "type": "address"},
                {"name": "tokenId", "type": "uint256"}
            ],
            "name": "hasAccess",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(self, rpc_url: str = None, contract_address: str = None):
        self.rpc_url = rpc_url or SEPOLIA_RPC_URL
        self.contract_address = contract_address or CONTRACT_ADDRESS
        
        if self.rpc_url:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        else:
            self.w3 = None
        
        if self.w3 and self.contract_address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.ABI
            )
        else:
            self.contract = None
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.contract is not None and self.w3.is_connected()
    
    def is_conversation_minted(self, conversation_id: str) -> bool:
        """检查对话是否已铸造"""
        if not self.is_configured():
            return False
        try:
            return self.contract.functions.isConversationMinted(conversation_id).call()
        except Exception as e:
            print(f"Error checking minted status: {e}")
            return False
    
    def get_token_by_conversation(self, conversation_id: str) -> Optional[int]:
        """通过对话 ID 获取 token ID"""
        if not self.is_configured():
            return None
        try:
            token_id = self.contract.functions.getTokenByConversation(conversation_id).call()
            return token_id if token_id > 0 else None
        except Exception as e:
            print(f"Error getting token: {e}")
            return None
    
    def get_nft_info(self, token_id: int) -> Optional[Dict]:
        """获取 NFT 信息"""
        if not self.is_configured():
            return None
        try:
            result = self.contract.functions.getNFTInfo(token_id).call()
            owner, nft, stake, reward = result
            
            rarity_names = ["Common", "Rare", "Epic", "Legendary"]
            
            return {
                "owner": owner,
                "nft": {
                    "conversationId": nft[0],
                    "ragId": nft[1],
                    "ipfsCID": nft[2],
                    "sparkValue": nft[3],
                    "baseScore": nft[4],
                    "citationScore": nft[5],
                    "activationScore": nft[6],
                    "behaviorScore": nft[7],
                    "rarity": rarity_names[nft[8]] if nft[8] < len(rarity_names) else "Unknown",
                    "creator": nft[9],
                    "createdAt": nft[10],
                    "isActive": nft[11],
                    "price": nft[12],
                    "totalSales": nft[13],
                    "totalRevenue": nft[14]
                },
                "stake": {
                    "amount": stake[0],
                    "stakedAt": stake[1],
                    "lockPeriod": stake[2],
                    "rewardRate": stake[3]
                },
                "reward": reward
            }
        except Exception as e:
            print(f"Error getting NFT info: {e}")
            return None
    
    def has_access(self, user_address: str, token_id: int) -> bool:
        """检查用户是否有访问权限"""
        if not self.is_configured():
            return False
        try:
            return self.contract.functions.hasAccess(
                Web3.to_checksum_address(user_address),
                token_id
            ).call()
        except Exception as e:
            print(f"Error checking access: {e}")
            return False


# 全局实例
nft_signer = SparkNFTSigner()
nft_contract = SparkNFTContract()

