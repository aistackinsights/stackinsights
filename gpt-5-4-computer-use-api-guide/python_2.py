response = client.responses.create(
    model="gpt-5.4",
    tools=[
        {"type": "computer"},
        {
            "type": "tool_search",
            # Your MCP servers registered here
            "mcp_servers": [
                {"server_url": "http://localhost:3000/mcp", "name": "my_tools"}
            ],
        },
    ],
    input=task,
)
