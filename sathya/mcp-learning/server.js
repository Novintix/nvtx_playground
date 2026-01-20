import express from "express";

const app = express();
app.use(express.json());

app.post("/mcp", (req, res) => {
  const { jsonrpc, id, method, params } = req.body;

  // Basic MCP validation
  if (jsonrpc !== "2.0") {
    return res.json({
      jsonrpc: "2.0",
      id,
      error: { message: "Invalid JSON-RPC version" },
    });
  }

  // Tool call
  if (method === "tools/call") {
    if (params.name === "helloTool") {
      return res.json({
        jsonrpc: "2.0",
        id,
        result: {
          content: [
            {
              type: "text",
              text: `Hello ${params.arguments.name}, MCP remote server is working 🎉`,
            },
          ],
        },
      });
    }

    return res.json({
      jsonrpc: "2.0",
      id,
      error: { message: "Tool not found" },
    });
  }

  res.json({
    jsonrpc: "2.0",
    id,
    error: { message: "Unknown method" },
  });
});

app.listen(3000, () => {
  console.log("✅ PURE MCP Server running at http://localhost:3000/mcp");
});
