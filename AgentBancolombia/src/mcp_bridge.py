import os
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

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

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Abre una conexión temporal por stdio, invoca la herramienta y retorna el resultado.
        """
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    text_response = result.content[0].text if result.content else "{}"
                    
                    #  INTERCEPCIÓN ERRORORES
                    if getattr(result, "isError", False) or getattr(result, "is_error", False) or text_response.startswith("Error"):
                        raise Exception(f"[{tool_name}] {text_response}")
                        
                    return text_response
        except Exception as e:
            raise Exception(f"El servidor MCP falló o no pudo iniciar : {str(e)}")