// 浏览器指纹获取函数
async function getBrowserFingerprint() {
    try {
        // 基本的浏览器信息收集
        const fingerprint = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screenResolution: `${window.screen.width}x${window.screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            cookiesEnabled: navigator.cookieEnabled,
            localStorage: !!window.localStorage,
            sessionStorage: !!window.sessionStorage,
        };

        // 生成指纹哈希
        const fingerprintStr = JSON.stringify(fingerprint);
        const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(fingerprintStr));
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        return hashHex;
    } catch (error) {
        console.error('获取浏览器指纹失败:', error);
        showFingerprintError();
        return null;
    }
}

// 显示错误提示
function showFingerprintError() {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fingerprint-error';
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background-color: #ff4444;
        color: white;
        padding: 15px 30px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1000;
    `;
    errorDiv.innerHTML = `
        <p style="margin: 0;">无法获取浏览器指纹，请确保启用了JavaScript并刷新页面重试。</p>
    `;
    document.body.appendChild(errorDiv);

    // 5秒后自动移除提示
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// 页面加载完成后自动获取指纹
document.addEventListener('DOMContentLoaded', async () => {
    const fingerprint = await getBrowserFingerprint();
    if (fingerprint) {
        // 如果成功获取到指纹，将其存储在隐藏的input中
        const fingerprintInput = document.createElement('input');
        fingerprintInput.type = 'hidden';
        fingerprintInput.name = 'browser_fingerprint';
        fingerprintInput.value = fingerprint;
        document.forms[0]?.appendChild(fingerprintInput);
    }
});