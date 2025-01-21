import os
import importlib.util
import Value.data as data


class PluginLoader:
    def __init__(self, terminal, plugin_dir="plugins"):
        self.terminal = terminal
        self.main_form = terminal  # 添加 main_form 引用
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.plugin_dir = os.path.join(current_dir, plugin_dir)
        self.plugins = {}  # 改为字典以便通过名称访问插件

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
                    self._register_commands(plugin)

        # 打印已注册的命令
        print(f"已注册的命令: {data.COMMANDS}")

    def _load_plugin(self, plugin_file):
        """加载单个插件"""
        global plugin_name
        try:
            plugin_name = os.path.splitext(os.path.basename(plugin_file))[0]
            print(f"正在加载插件: {plugin_file}")

            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            plugin_class = getattr(module, f"{plugin_name.replace('_', '').capitalize()}")
            plugin_instance = plugin_class()

            # 设置插件的必要属性
            plugin_instance.plugin_loader = self
            plugin_instance.main_form = self.main_form

            # 将插件保存到字典中
            self.plugins[plugin_name] = plugin_instance

            return plugin_instance
        except Exception as e:
            print(f"加载插件失败 {plugin_name}: {str(e)}")
            return None

    def get_loaded_plugins(self):
        """返回已加载插件的列表"""
        return list(self.plugins.keys())

    def _register_commands(self, plugin):
        """注册插件的命令"""
        try:
            commands = plugin.get_commands()
            for cmd_name, cmd_func in commands.items():
                if isinstance(cmd_func, str):
                    # 如果是字符串，则获取对应的方法
                    self.terminal.register_command(cmd_name, getattr(plugin, cmd_func))
                else:
                    # 如果直接是方法对象，则直接注册
                    self.terminal.register_command(cmd_name, cmd_func)
        except Exception as e:
            print(f"注册命令失败: {str(e)}")

    def get_plugins(self):
        """获取所有已加载的插件"""
        return self.plugins

    def get_all_help(self) -> str:
        """获取所有插件的帮助信息"""
        help_text = "\n插件命令："
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'get_help'):
                    help_text += "\n" + plugin.get_help()
            except Exception as e:
                print(f"获取插件 {plugin_name} 的帮助信息失败: {str(e)}")
        return help_text

