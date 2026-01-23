const response = await fetch("http://localhost:3000/mcp", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    method: "tools/call",
    params: {
      name: "helloTool",
      arguments: {
        name: "Sathya",
      },
    },
  }),
});

const data = await response.json();
console.log(data.result.content[0].text);
