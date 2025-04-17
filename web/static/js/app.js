document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // 添加可爱欢迎消息
    addAIMessage("你好呀！我是可爱的Synapse AI助手~ 🌸 有什么可以帮你的吗？");

    // 发送消息处理
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            // 添加用户消息
            addUserMessage(message);
            userInput.value = '';
            
            // 显示思考中状态
            const thinkingMsg = addAIMessage("思考中... 🧠", true);
            
            // 发送消息到后端API
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // 移除"思考中"消息
                thinkingMsg.remove();
                
                // 显示API回复
                if (data.status === 'success') {
                    addAIMessage(data.reply);
                } else {
                    addAIMessage("哎呀，出错了呢... 😅 请再试一次~");
                }
                
                // 滚动到底部
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                thinkingMsg.remove();
                addAIMessage("网络连接出现问题啦... 🌐 请检查网络后重试");
                console.error('Error:', error);
            });
        }
    }

    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    function addAIMessage(text, isThinking = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ai-message ${isThinking ? 'thinking' : ''}`;
        messageDiv.innerHTML = isThinking ? text : `AI: ${text}`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }
});