from flask import Flask, request, render_template_string


class Application:
    """应用程序主类"""
    
    def __init__(self):
        # 初始化配置
        self.config = load_config()
        
        # 初始化日志
        self.logger = LogConfig.get_instance().get_logger("main", "__main__.log")
        
        # 初始化消息总线
        self.message_bus = MessageBus()
        
        # 初始化组件
        self.console_input = ConsoleInputHandler(self.message_bus)
        self.console_output = ConsoleOutputHandler(self.message_bus)
        self.agent = AgentCore(self.message_bus, self.config)
        
        # 组件列表,用于批量启动和停止
        self.components = [
            self.message_bus,
            self.console_input,
            self.console_output,
            self.agent
        ]
        
        # 初始化Flask应用
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/submit', 'submit', self.submit, methods=['POST'])
        
    async def start(self):
        """启动应用程序"""
        try:
            self.logger.info("正在启动应用程序...")
            
            # 按顺序启动所有组件
            for component in self.components:
                await component.start()
                
            self.logger.info("应用程序启动完成")
            
            # 启动Flask应用
            from threading import Thread
            thread = Thread(target=self.app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
            thread.daemon = True
            thread.start()
            
            # 等待直到收到退出信号
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("收到退出信号")
        except Exception as e:
            self.logger.error(f"应用程序运行错误: {str(e)}")
        finally:
            await self.stop()
            
    def index(self):
        return render_template_string('''
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <title>Synapse AI Agent</title>
              </head>
              <body>
                <div class="container">
                  <h1>Synapse AI Agent</h1>
                  <form method="post" action="/submit">
                    <div class="form-group">
                      <label for="input">输入:</label>
                      <input type="text" class="form-control" id="input" name="input" required>
                    </div>
                    <button type="submit" class="btn btn-primary">提交</button>
                  </form>
                  <div id="output"></div>
                </div>
                <script>
                  document.querySelector('form').addEventListener('submit', async function(event) {
                    event.preventDefault();
                    const input = document.querySelector('#input').value;
                    const response = await fetch('/submit', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                      },
                      body: new URLSearchParams({ input: input }),
                    });
                    const data = await response.json();
                    document.querySelector('#output').innerText = 'AI: ' + data.response;
                  });
                </script>
              </body>
            </html>
        ''')
        
    def submit(self):
        input_text = request.form['input']
        self.logger.info(f"收到输入: {input_text}")
        response = self.agent.process_input(input_text)
        return {'response': response}

def main():
    """程序入口"""
    app = Application()
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"程序异常退出: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()