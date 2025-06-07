// 测试代理连接的简单脚本
// 在浏览器控制台中运行

async function testAgentConnection(baseUrl) {
    console.log(`测试代理连接: ${baseUrl}`);
    
    try {
        // 测试代理卡片获取
        const cardUrl = `${baseUrl}/.well-known/agent.json`;
        console.log(`获取代理卡片: ${cardUrl}`);
        
        const response = await fetch(cardUrl);
        console.log(`响应状态: ${response.status} ${response.statusText}`);
        console.log(`响应头:`, Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
        }
        
        const cardData = await response.json();
        console.log(`代理卡片数据:`, cardData);
        
        // 测试代理端点
        const agentEndpoint = cardData.url;
        console.log(`代理端点: ${agentEndpoint}`);
        
        // 测试简单的ping请求
        try {
            const pingResponse = await fetch(agentEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "ping",
                    id: "test-ping"
                })
            });
            console.log(`Ping响应状态: ${pingResponse.status}`);
        } catch (pingError) {
            console.log(`Ping测试失败 (这是正常的):`, pingError.message);
        }
        
        return cardData;
        
    } catch (error) {
        console.error(`代理连接测试失败:`, error);
        throw error;
    }
}

// 测试所有预设代理
async function testAllAgents() {
    const agents = [
        'http://localhost:10003',
        'http://localhost:10004', 
        'http://localhost:10005',
        'http://localhost:10006'
    ];
    
    for (const agent of agents) {
        console.log(`\n=== 测试 ${agent} ===`);
        try {
            await testAgentConnection(agent);
            console.log(`✅ ${agent} 连接成功`);
        } catch (error) {
            console.log(`❌ ${agent} 连接失败:`, error.message);
        }
    }
}

// 使用方法:
// 在浏览器控制台中运行:
// testAgentConnection('http://localhost:10005')
// 或者测试所有代理:
// testAllAgents()

console.log('代理连接测试脚本已加载');
console.log('使用方法:');
console.log('testAgentConnection("http://localhost:10005")');
console.log('testAllAgents()');
