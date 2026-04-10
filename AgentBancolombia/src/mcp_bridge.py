import os
import asyncio
import threading
import contextlib
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

class PersistentMCPBridge:
    """
    Singleton que mantiene vivo el Servidor MCP por stdio en un hilo en segundo plano.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Patrón Singleton thread-safe para garantizar que solo exista una instancia
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PersistentMCPBridge, cls).__new__(cls)
                cls._instance._init_background_thread()
        return cls._instance

    def _init_background_thread(self):
        """Inicializa el hilo y espera a que la conexión MCP se establezca."""
        print("[INFO] Iniciando hilo en segundo plano para MCP Server...")
        self.loop = asyncio.new_event_loop()
        
        # El daemon=True asegura que el hilo muera si Streamlit se apaga
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()
        
        self._exit_stack = contextlib.AsyncExitStack()
        self.session = None
        self._connected = False
        
        # Obligamos al hilo principal de Streamlit a esperar hasta que el MCP esté listo
        future = asyncio.run_coroutine_threadsafe(self._connect_async(), self.loop)
        future.result() 

    def _start_loop(self):
        """Mantiene vivo el ciclo asíncrono permanentemente."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect_async(self):
        """Lógica asíncrona interna para arrancar el servidor stdio."""
        if self._connected:
            return

        server_dir = os.path.abspath("McpServerBancolombia")
        env = os.environ.copy()
        env["PYTHONPATH"] = server_dir + os.pathsep + env.get("PYTHONPATH", "")

        server_params = StdioServerParameters(
            command="python",
            args=["-u", "-m", "app.main"], 
            env=env
        )
        
        try:
            read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()
            self._connected = True
            print("[INFO] Conexión MCP persistente establecida en segundo plano.")
        except Exception as e:
            print(f"[ERROR CRÍTICO] Falló al iniciar MCP en background: {str(e)}")
            raise e

    def call_tool_sync(self, tool_name: str, arguments: dict) -> str:
        """
        Método sincrónico que las Tools llamarán.
        Envía la tarea al hilo en segundo plano y bloquea hasta tener la respuesta.
        """
        if not self._connected or self.session is None:
            # Reconexión de emergencia
            future = asyncio.run_coroutine_threadsafe(self._connect_async(), self.loop)
            future.result()

        # Enviamos la ejecución al loop persistente
        future = asyncio.run_coroutine_threadsafe(
            self._call_tool_async(tool_name, arguments), self.loop
        )
        return future.result() # Bloquea el hilo de Streamlit hasta que llega el resultado

    async def _call_tool_async(self, tool_name: str, arguments: dict) -> str:
        """La ejecución asíncrona real de la herramienta."""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            
            text_response = result.content[0].text if result.content else ""
            has_native_error = getattr(result, "isError", False) or getattr(result, "is_error", False)
            has_text_error = text_response.strip().startswith("Error")
            
            if has_native_error or has_text_error:
                 raise Exception(f"{text_response}")
                 
            return text_response
        except Exception as e:
            raise Exception(f"Error interno MCP: {str(e)}")