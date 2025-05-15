document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages')
  const userInput = document.getElementById('user-input')
  const sendBtn = document.getElementById('send-btn')

  // 添加可爱欢迎消息
  addAIMessage('你好呀！我是可爱的Synapse AI助手~ 🌸 有什么可以帮你的吗？')

  // 发送消息处理
  sendBtn.addEventListener('click', (e) => {
    e.preventDefault()
    sendMessage()
  })
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      sendMessage()
    }
  })

  function sendMessage() {
    const message = userInput.value.trim()
    if (!message) return
    addUserMessage(message)
    userInput.value = ''
    const thinkingMsg = addAIMessage('思考中... 🧠', true)
    // 生成/获取user_id（可用localStorage/sessionStorage持久化）
    let userId = localStorage.getItem('user_id')
    if (!userId) {
      userId = Math.random().toString(36).substring(2) + Date.now()
      localStorage.setItem('user_id', userId)
    }
    fetch('/api/v1/agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ message: message, user_id: userId }),
    })
      .then((response) => response.json())
      .then((data) => {
        thinkingMsg.remove()
        if (data.status === 'success') {
          addAIMessage(data.reply)
        } else {
          addAIMessage('哎呀，出错了呢... 😅 请再试一次~')
        }
        chatMessages.scrollTop = chatMessages.scrollHeight
      })
      .catch((error) => {
        thinkingMsg.remove()
        addAIMessage('网络连接出现问题啦... 🌐 请检查网络后重试')
        console.error('Error:', error)
      })
  }

  function addUserMessage(text) {
    const messageDiv = document.createElement('div')
    messageDiv.className = 'message user-message'
    messageDiv.textContent = text
    chatMessages.appendChild(messageDiv)
    chatMessages.scrollTop = chatMessages.scrollHeight
    return messageDiv
  }

  function addAIMessage(text, isThinking = false) {
    const messageDiv = document.createElement('div')
    messageDiv.className = `message ai-message ${isThinking ? 'thinking' : ''}`
    messageDiv.innerHTML = isThinking ? text : `AI: ${text}`
    chatMessages.appendChild(messageDiv)
    chatMessages.scrollTop = chatMessages.scrollHeight
    return messageDiv
  }
})
