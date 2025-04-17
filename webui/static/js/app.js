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
            
            // 模拟AI思考动画
            const thinkingMsg = addAIMessage("思考中... 🧠", true);
            
        
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