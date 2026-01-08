"""
讨论大厅模块
- 实时群聊功能
- 基于 RAG 的讨论室
- 1小时窗口内的用户自动匹配
"""
import asyncio
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
import uuid


@dataclass
class DiscussionMessage:
    """讨论消息"""
    id: str
    user_id: str
    username: str
    content: str
    timestamp: float
    message_type: str = "text"  # text, system, rag_context
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "formatted_time": datetime.fromtimestamp(self.timestamp).strftime("%H:%M"),
        }


@dataclass
class DiscussionRoom:
    """讨论室"""
    room_id: str
    rag_id: str
    created_at: float
    messages: List[DiscussionMessage] = field(default_factory=list)
    active_users: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # user_id -> {username, joined_at, last_active}
    websockets: Dict[str, WebSocket] = field(default_factory=dict)  # user_id -> WebSocket
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "rag_id": self.rag_id,
            "created_at": self.created_at,
            "user_count": len(self.active_users),
            "users": [
                {"user_id": uid, "username": info["username"]}
                for uid, info in self.active_users.items()
            ],
            "message_count": len(self.messages),
        }


class DiscussionManager:
    """讨论室管理器"""
    
    def __init__(self, window_hours: float = 1.0):
        self.rooms: Dict[str, DiscussionRoom] = {}  # room_id -> DiscussionRoom
        self.rag_rooms: Dict[str, str] = {}  # rag_id -> room_id (当前活跃的讨论室)
        self.user_access_times: Dict[str, Dict[str, float]] = defaultdict(dict)  # rag_id -> {user_id -> access_time}
        self.window_hours = window_hours
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """定期清理过期用户"""
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            await self._cleanup_expired_users()
    
    async def _cleanup_expired_users(self):
        """清理超时用户"""
        current_time = time.time()
        window_seconds = self.window_hours * 3600
        
        for room_id, room in list(self.rooms.items()):
            expired_users = []
            
            for user_id, info in room.active_users.items():
                if current_time - info["last_active"] > window_seconds:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                await self._remove_user_from_room(room, user_id, "timeout")
            
            # 如果房间空了，可以选择保留或删除
            if not room.active_users:
                # 保留房间但标记为空闲
                pass
    
    async def _remove_user_from_room(self, room: DiscussionRoom, user_id: str, reason: str = "left"):
        """从房间移除用户"""
        if user_id in room.active_users:
            username = room.active_users[user_id]["username"]
            del room.active_users[user_id]
            
            # 关闭 WebSocket
            if user_id in room.websockets:
                try:
                    ws = room.websockets[user_id]
                    await ws.close()
                except:
                    pass
                del room.websockets[user_id]
            
            # 发送系统消息
            system_msg = DiscussionMessage(
                id=str(uuid.uuid4()),
                user_id="system",
                username="系统",
                content=f"{username} 已离开讨论（{reason}）",
                timestamp=time.time(),
                message_type="system",
            )
            room.messages.append(system_msg)
            await self._broadcast_to_room(room, system_msg.to_dict())
    
    async def _broadcast_to_room(self, room: DiscussionRoom, message: Dict[str, Any]):
        """向房间内所有用户广播消息"""
        disconnected = []
        for user_id, ws in room.websockets.items():
            try:
                await ws.send_json({"type": "message", "data": message})
            except:
                disconnected.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected:
            await self._remove_user_from_room(room, user_id, "disconnected")
    
    def record_rag_access(self, rag_id: str, user_id: str):
        """记录用户访问 RAG 的时间"""
        self.user_access_times[rag_id][user_id] = time.time()
    
    def get_recent_users(self, rag_id: str) -> List[str]:
        """获取最近1小时内访问过该 RAG 的用户"""
        current_time = time.time()
        window_seconds = self.window_hours * 3600
        
        recent_users = []
        if rag_id in self.user_access_times:
            for user_id, access_time in self.user_access_times[rag_id].items():
                if current_time - access_time <= window_seconds:
                    recent_users.append(user_id)
        
        return recent_users
    
    def get_or_create_room(self, rag_id: str) -> DiscussionRoom:
        """获取或创建 RAG 对应的讨论室"""
        if rag_id in self.rag_rooms:
            room_id = self.rag_rooms[rag_id]
            if room_id in self.rooms:
                return self.rooms[room_id]
        
        # 创建新房间
        room_id = f"room_{rag_id}_{int(time.time())}"
        room = DiscussionRoom(
            room_id=room_id,
            rag_id=rag_id,
            created_at=time.time(),
        )
        self.rooms[room_id] = room
        self.rag_rooms[rag_id] = room_id
        
        return room
    
    async def join_room(
        self, 
        room: DiscussionRoom, 
        user_id: str, 
        username: str, 
        websocket: WebSocket
    ) -> bool:
        """用户加入讨论室"""
        current_time = time.time()
        
        # 添加用户
        room.active_users[user_id] = {
            "username": username,
            "joined_at": current_time,
            "last_active": current_time,
        }
        room.websockets[user_id] = websocket
        
        # 发送系统消息
        system_msg = DiscussionMessage(
            id=str(uuid.uuid4()),
            user_id="system",
            username="系统",
            content=f"{username} 加入了讨论",
            timestamp=current_time,
            message_type="system",
        )
        room.messages.append(system_msg)
        
        # 广播给其他用户
        await self._broadcast_to_room(room, system_msg.to_dict())
        
        # 发送最近的消息历史给新用户
        recent_messages = room.messages[-50:]  # 最近50条
        try:
            await websocket.send_json({
                "type": "history",
                "data": {
                    "room": room.to_dict(),
                    "messages": [m.to_dict() for m in recent_messages],
                }
            })
        except:
            return False
        
        return True
    
    async def leave_room(self, room_id: str, user_id: str):
        """用户离开讨论室"""
        if room_id in self.rooms:
            await self._remove_user_from_room(self.rooms[room_id], user_id, "离开")
    
    async def send_message(
        self, 
        room_id: str, 
        user_id: str, 
        username: str, 
        content: str
    ) -> Optional[DiscussionMessage]:
        """发送消息"""
        if room_id not in self.rooms:
            return None
        
        room = self.rooms[room_id]
        
        if user_id not in room.active_users:
            return None
        
        # 更新用户活跃时间
        room.active_users[user_id]["last_active"] = time.time()
        
        # 创建消息
        message = DiscussionMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            username=username,
            content=content,
            timestamp=time.time(),
            message_type="text",
        )
        room.messages.append(message)
        
        # 广播
        await self._broadcast_to_room(room, message.to_dict())
        
        return message
    
    def get_all_public_rooms(self) -> List[Dict[str, Any]]:
        """获取所有公开讨论室列表"""
        return [room.to_dict() for room in self.rooms.values()]
    
    def get_room_by_id(self, room_id: str) -> Optional[DiscussionRoom]:
        """通过 ID 获取讨论室"""
        return self.rooms.get(room_id)


# 全局讨论管理器实例
discussion_manager = DiscussionManager(window_hours=1.0)

