import os
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import contextlib

class MCPBridge:
    """
    Clase encargada de gestionar la conexión por stdio con el Servidor MCP.
    """
    def __init__(self):
        # 1. Obtenemos la ruta absoluta a la carpeta del servidor
        server_dir = os.path.abspath("McpServerBancolombia")
        
        # 2. Inyectamos esa ruta en el PYTHONPATH del subproceso
        env = os.environ.copy()
        env["PYTHONPATH"] = server_dir + os.pathsep + env.get("PYTHONPATH", "")

        # 3. Configuramos los parámetros forzando la ejecución como módulo (-m app.main)
        self.server_params = StdioServerParameters(
            command="python",
            args=["-u", "-m", "app.main"], 
            env=env
        )
        
        # Variables para mantener el estado de la conexión
        self._exit_stack = contextlib.AsyncExitStack()
        self.session: ClientSession | None = None
        self._connected = False

    async def connect(self):
        """
        Inicia el servidor MCP y establece la sesión. 
        Se llama una vez al iniciar la app.
        """
        if self._connected:
            return

        try:
            # 1. Abrimos el cliente stdio y lo mantenemos abierto con AsyncExitStack
            read, write = await self._exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            
            # 2. Creamos la sesión y la inicializamos
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self.session.initialize()
            
            self._connected = True
            print("[INFO] Conexión MCP establecida y persistente.")
            
        except Exception as e:
            await self.disconnect()
            raise Exception(f"El servidor MCP falló o no pudo iniciar: {str(e)}")
    
    async def disconnect(self):
        """Cierra el servidor MCP de forma limpia."""
        self._connected = False
        self.session = None
        await self._exit_stack.aclose()
        print("[INFO] Conexión MCP cerrada.")

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Ejecuta una herramienta usando la sesión ya abierta.
        """

        if not self._connected or self.session is None:
            # Si por alguna razón no está conectado (ej. reinicio de Streamlit), reconectamos
            await self.connect()

        text_response = ""
        has_logical_error = False

        try:
            # Reutilizamos la sesión viva
            result = await self.session.call_tool(tool_name, arguments)
            
            text_response = result.content[0].text if result.content else ""
            has_native_error = getattr(result, "isError", False) or getattr(result, "is_error", False)
            has_text_error = text_response.strip().startswith("Error")
            
            if has_native_error or has_text_error:
                has_logical_error = True
                        
        except Exception as e:
            raise Exception(f"El Servidor MCP se cerró inesperadamente: {str(e)}")

        if has_logical_error:
             raise Exception(f"{text_response}")
             
        return text_response