import os
import importlib.util
import Value.data as data

class PluginLoader:
    def __init__(self, terminal, plugin_dir="plugins"):
        self.terminal = terminal
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建插件目录的绝对路径
        self.plugin_dir = os.path.join(current_dir, plugin_dir)
        self.plugins = []

    def load_plugins(self):
        """加载所有插件"""
        print("开始加载插件...")
        print(f"正在从 {self.plugin_dir} 加载插件...")
        print(f"插件目录的绝对路径: {os.path.abspath(self.plugin_dir)}")

        # 确保插件目录存在
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            print(f"创建插件目录: {self.plugin_dir}")
            return

        # 遍历插件目录
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py'):
                plugin_path = os.path.join(self.plugin_dir, filename)
                plugin = self._load_plugin(plugin_path)
                if plugin:
                    self.plugins.append(plugin)
                    self._register_commands(plugin)

        # 打印已注册的命令
        print(f"已注册的命令: {data.COMMANDS}")

    def _load_plugin(self, plugin_file):
        """加载单个插件"""
        try:
            plugin_name = os.path.splitext(os.path.basename(plugin_file))[0]
            print(f"正在加载插件: {plugin_file}")

            # 导入模块
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 获取插件类
            plugin_class = getattr(module, f"{plugin_name.replace('_', '').capitalize()}")

            return plugin_class()
        except Exception as e:
            print(f"加载插件失败 {plugin_name}: {str(e)}")
            return None

    def _register_commands(self, plugin):
        """注册插件的命令"""
        try:
            commands = plugin.get_commands()
            for cmd_name, cmd_func in commands.items():
                self.terminal.register_command(cmd_name, getattr(plugin, cmd_func))
        except Exception as e:
            print(f"注册命令失败: {str(e)}")

    def get_plugins(self):
        """获取所有已加载的插件"""
        return self.plugins
