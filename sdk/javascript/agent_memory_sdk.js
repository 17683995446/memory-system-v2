/**
 * JavaScript SDK for Agent Memory System
 * 基于第一性原理：简洁、易用、可靠
 */

class AgentMemoryClient {
    constructor(baseUrl = "http://localhost:5000", timeout = 30000) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.timeout = timeout;
    }

    async health() {
        return this._request('GET', '/health');
    }

    async addMemory(text, sessionId = "default", level = "l2", metadata = null) {
        const data = {
            text: text,
            session_id: sessionId,
            level: level
        };
        if (metadata) {
            data.metadata = metadata;
        }
        return this._request('POST', '/api/v1/memory', data);
    }

    async getMemory(memoryId) {
        return this._request('GET', `/api/v1/memory/${memoryId}`);
    }

    async deleteMemory(memoryId) {
        return this._request('DELETE', `/api/v1/memory/${memoryId}`);
    }

    async recall(query, sessionId = "default", limit = null) {
        const data = {
            query: query,
            session_id: sessionId
        };
        if (limit) {
            data.limit = limit;
        }
        return this._request('POST', '/api/v1/recall', data);
    }

    async addFact(entity, attribute, value) {
        return this._request('POST', '/api/v1/fact', {
            entity: entity,
            attribute: attribute,
            value: value
        });
    }

    async queryFacts(entity = null, attribute = null) {
        const params = {};
        if (entity) params.entity = entity;
        if (attribute) params.attribute = attribute;
        return this._request('GET', '/api/v1/facts', null, params);
    }

    async getStats() {
        return this._request('GET', '/api/v1/stats');
    }

    async preprocess(text, checkHallucination = false) {
        return this._request('POST', '/api/v1/preprocess', {
            text: text,
            check_hallucination: checkHallucination
        });
    }

    async cleanup(level = "l2", days = null) {
        const data = { level: level };
        if (days) data.days = days;
        return this._request('POST', '/api/v1/governance/cleanup', data);
    }

    // 批量操作
    async batchAddMemories(memories, sessionId = "default") {
        const results = [];
        for (const memory of memories) {
            const result = await this.addMemory(
                memory.text,
                sessionId,
                memory.level || "l2",
                memory.metadata
            );
            results.push(result);
        }
        return {
            success: true,
            total: results.length,
            results: results
        };
    }

    async batchRecall(queries, sessionId = "default") {
        const results = {};
        for (const query of queries) {
            results[query] = await this.recall(query, sessionId);
        }
        return {
            success: true,
            queries: queries.length,
            results: results
        };
    }

    async _request(method, path, data = null, params = null) {
        const url = new URL(`${this.baseUrl}${path}`);
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            signal: AbortSignal.timeout(this.timeout)
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        if (params) {
            for (const [key, value] of Object.entries(params)) {
                url.searchParams.append(key, value);
            }
        }

        const response = await fetch(url.toString(), options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `HTTP error! status: ${response.status}`);
        }
        
        return result;
    }
}

// 便捷函数
function createClient(baseUrl = "http://localhost:5000") {
    return new AgentMemoryClient(baseUrl);
}

// Node.js导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AgentMemoryClient,
        createClient
    };
}
