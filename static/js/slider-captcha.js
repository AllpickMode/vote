
class SliderCaptcha {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            width: options.width || 280,
            height: options.height || 155,
            sliderWidth: options.sliderWidth || 40,
            sliderHeight: options.sliderHeight || 40,
            onSuccess: options.onSuccess || function() {},
            onFail: options.onFail || function() {},
            onRefresh: options.onRefresh || function() {}
        };
        this.captchaData = null;
        this.isDragging = false;
        this.animationFrame = null;
        this.destroyed = false;
        this.init();
        
        // 添加清理方法
        this.destroy = () => {
            this.destroyed = true;
            if (this.animationFrame) {
                cancelAnimationFrame(this.animationFrame);
                this.animationFrame = null;
            }
            // 移除所有事件监听器
            this.slider.removeEventListener('mousedown', this.downHandler);
            this.slider.removeEventListener('touchstart', this.downHandler);
            // 清除DOM元素
            this.element.innerHTML = '';
        };

        // 确保在页面卸载时清理资源
        window.addEventListener('unload', this.destroy);
    }

    startDragging() {
        this.isDragging = true;
        this.slider.style.cursor = 'grabbing';
        document.body.style.cursor = 'grabbing';
    }

    stopDragging() {
        this.isDragging = false;
        this.slider.style.cursor = 'grab';
        document.body.style.cursor = 'default';
    }

    async init() {
        this.createCanvas();
        this.createSlider();
        this.bindEvents();
        await this.refresh();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'slider-captcha-canvas';
        this.canvas.width = this.options.width;
        this.canvas.height = this.options.height;
        this.element.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
    }

    createSlider() {
        this.slider = document.createElement('div');
        this.slider.className = 'slider-captcha-handle';
        this.sliderTrack = document.createElement('div');
        this.sliderTrack.className = 'slider-captcha-track';
        this.sliderTrack.appendChild(this.slider);
        this.element.appendChild(this.sliderTrack);
    }

    async getCaptchaData() {
        try {
            const response = await fetch('/api/captcha/generate');
            if (!response.ok) throw new Error('获取验证码失败');
            return await response.json();
        } catch (error) {
            console.error('获取验证码失败:', error);
            throw error;
        }
    }

    async verifyCaptcha(position) {
        try {
            const response = await fetch('/api/captcha/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    position: position,
                    token: this.captchaData.token
                })
            });
            return await response.json();
        } catch (error) {
            console.error('验证失败:', error);
            return { success: false, message: '验证请求失败' };
        }
    }

    bindEvents() {
        let startX = 0;
        let currentX = 0;
        let rafId = null;

        const updateSliderPosition = (moveX) => {
            if (this.destroyed) return;
            
            this.slider.style.transform = `translate3d(${moveX}px, 0, 0)`;
            currentX = moveX;

            if (rafId) {
                cancelAnimationFrame(rafId);
            }

            rafId = requestAnimationFrame(() => {
                if (this.destroyed) return;
                
                this.ctx.clearRect(0, 0, this.options.width, this.options.height);
                this.drawBackground();
                
                const y = this.options.height / 2 - this.options.sliderHeight / 2;
                
                // 绘制滑动轨迹
                this.ctx.fillStyle = 'rgba(117, 184, 62, 0.1)';
                this.ctx.fillRect(0, y, moveX + this.options.sliderWidth, this.options.sliderHeight);
                
                // 绘制目标位置（半透明）
                this.ctx.fillStyle = 'rgba(117, 184, 62, 0.3)';
                this.ctx.fillRect(this.captchaData.target_pos, y, this.options.sliderWidth, this.options.sliderHeight);
                
                // 绘制当前滑块位置
                this.ctx.fillStyle = '#75b83e';
                this.ctx.fillRect(moveX, y, this.options.sliderWidth, this.options.sliderHeight);
                
                // 绘制滑块内部纹理
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                this.ctx.fillRect(moveX + this.options.sliderWidth/3, y + 10, 2, this.options.sliderHeight - 20);
                this.ctx.fillRect(moveX + this.options.sliderWidth*2/3, y + 10, 2, this.options.sliderHeight - 20);
            });
        };

        const moveHandler = (e) => {
            if (!this.isDragging || this.destroyed) return;
            e.preventDefault();
            
            const touch = e.type === 'touchmove' ? e.touches[0] : e;
            let moveX = touch.clientX - startX;
            moveX = Math.max(0, Math.min(moveX, this.options.width - this.options.sliderWidth));
            
            updateSliderPosition(moveX);
        };

        const upHandler = async () => {
            if (!this.isDragging || this.destroyed) return;
            this.stopDragging();
            
            document.removeEventListener('mousemove', moveHandler, { passive: false });
            document.removeEventListener('touchmove', moveHandler, { passive: false });
            document.removeEventListener('mouseup', upHandler);
            document.removeEventListener('touchend', upHandler);

            if (rafId) {
                cancelAnimationFrame(rafId);
                rafId = null;
            }

            try {
                // 验证滑块位置
                const result = await this.verifyCaptcha(currentX);
                if (this.destroyed) return;

                if (result.success) {
                    // 成功状态的视觉效果
                    this.sliderTrack.classList.add('success');
                    this.drawSuccessState();
                    // 更新验证token
                    document.getElementById('verificationToken').value = result.verification_token;
                    this.options.onSuccess();
                } else {
                    // 失败状态的视觉效果
                    this.sliderTrack.classList.add('fail');
                    this.drawFailState();
                    setTimeout(() => {
                        if (!this.destroyed) {
                            this.reset();
                            this.refresh();
                        }
                    }, 1000);
                    this.options.onFail();
                }
            } catch (error) {
                console.error('验证请求失败:', error);
                this.sliderTrack.classList.add('fail');
                this.drawFailState();
                setTimeout(() => {
                    if (!this.destroyed) {
                        this.reset();
                        this.refresh();
                    }
                }, 1000);
                this.options.onFail();
            }
        };

        const downHandler = (e) => {
            if (this.destroyed) return;
            e.preventDefault();
            
            this.startDragging();
            const touch = e.type === 'touchstart' ? e.touches[0] : e;
            startX = touch.clientX - (this.slider.getBoundingClientRect().left - this.element.getBoundingClientRect().left);
            
            document.addEventListener('mousemove', moveHandler, { passive: false });
            document.addEventListener('touchmove', moveHandler, { passive: false });
            document.addEventListener('mouseup', upHandler);
            document.addEventListener('touchend', upHandler);
        };

        // 保存handler引用以便清理
        this.downHandler = downHandler;
        
        this.slider.addEventListener('mousedown', this.downHandler);
        this.slider.addEventListener('touchstart', this.downHandler, { passive: false });
    }

    async refresh() {
        try {
            this.captchaData = await this.getCaptchaData();
            this.ctx.clearRect(0, 0, this.options.width, this.options.height);
            this.drawBackground();
            this.drawPuzzle();
            this.reset();
            this.options.onRefresh();
        } catch (error) {
            console.error('刷新验证码失败:', error);
        }
    }

    reset() {
        this.slider.style.transition = 'transform 0.3s ease';
        this.slider.style.transform = 'translate3d(0px, 0, 0)';
        this.sliderTrack.classList.remove('success', 'fail');
        document.getElementById('verificationToken').value = '';
        setTimeout(() => {
            this.slider.style.transition = '';
        }, 300);
    }

    drawBackground() {
        // 绘制主背景
        this.ctx.fillStyle = '#f3f4f6';
        this.ctx.fillRect(0, 0, this.options.width, this.options.height);
        
        // 添加网格效果
        this.ctx.strokeStyle = '#e5e7eb';
        this.ctx.lineWidth = 0.5;
        
        // 绘制垂直线
        for (let x = 0; x <= this.options.width; x += 20) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.options.height);
            this.ctx.stroke();
        }
        
        // 绘制水平线
        for (let y = 0; y <= this.options.height; y += 20) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.options.width, y);
            this.ctx.stroke();
        }

        // 如果是初始状态，添加提示动画
        if (!this.isDragging && !this.sliderTrack.classList.contains('success') && !this.sliderTrack.classList.contains('fail')) {
            const y = this.options.height / 2 - this.options.sliderHeight / 2;
            
            // 计算提示动画的位置
            const time = Date.now() / 1000;
            const x = Math.sin(time * 2) * 10 + 10;  // 在0-20像素范围内轻微摆动
            
            // 绘制提示箭头
            this.ctx.fillStyle = 'rgba(117, 184, 62, 0.5)';
            this.ctx.beginPath();
            this.ctx.moveTo(x + 40, y + this.options.sliderHeight / 2);
            this.ctx.lineTo(x + 55, y + this.options.sliderHeight / 2);
            this.ctx.lineTo(x + 50, y + this.options.sliderHeight / 2 - 5);
            this.ctx.lineTo(x + 50, y + this.options.sliderHeight / 2 + 5);
            this.ctx.fill();
            
            // 触发重绘
            if (!this.animationFrame) {
                this.animationFrame = requestAnimationFrame(() => {
                    this.animationFrame = null;
                    this.drawBackground();
                });
            }
        }
    }

    drawPuzzle() {
        if (!this.captchaData) return;
        
        const y = this.options.height / 2 - this.options.sliderHeight / 2;
        
        // 绘制目标位置（半透明）
        this.ctx.fillStyle = 'rgba(117, 184, 62, 0.3)';
        this.ctx.fillRect(this.captchaData.target_pos, y, this.options.sliderWidth, this.options.sliderHeight);
        
        // 绘制初始滑块位置
        this.ctx.fillStyle = '#75b83e';
        this.ctx.fillRect(0, y, this.options.sliderWidth, this.options.sliderHeight);
    }

    drawSuccessState() {
        const y = this.options.height / 2 - this.options.sliderHeight / 2;
        
        // 清除画布
        this.ctx.clearRect(0, 0, this.options.width, this.options.height);
        this.drawBackground();
        
        // 绘制成功状态的轨迹
        this.ctx.fillStyle = 'rgba(117, 184, 62, 0.2)';
        this.ctx.fillRect(0, y, this.captchaData.target_pos + this.options.sliderWidth, this.options.sliderHeight);
        
        // 绘制成功位置的滑块
        this.ctx.fillStyle = '#75b83e';
        this.ctx.fillRect(this.captchaData.target_pos, y, this.options.sliderWidth, this.options.sliderHeight);
        
        // 绘制成功标记（对勾）
        this.ctx.beginPath();
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;
        this.ctx.moveTo(this.captchaData.target_pos + 12, y + 20);
        this.ctx.lineTo(this.captchaData.target_pos + 17, y + 25);
        this.ctx.lineTo(this.captchaData.target_pos + 28, y + 15);
        this.ctx.stroke();
    }

    drawFailState() {
        const y = this.options.height / 2 - this.options.sliderHeight / 2;
        
        // 清除画布
        this.ctx.clearRect(0, 0, this.options.width, this.options.height);
        this.drawBackground();
        
        // 绘制失败状态的轨迹
        this.ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
        this.ctx.fillRect(0, y, this.options.width, this.options.sliderHeight);
        
        // 绘制目标位置（红色）
        this.ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
        this.ctx.fillRect(this.captchaData.target_pos, y, this.options.sliderWidth, this.options.sliderHeight);
        
        // 绘制当前位置的滑块（红色）
        this.ctx.fillStyle = '#ef4444';
        this.ctx.fillRect(0, y, this.options.sliderWidth, this.options.sliderHeight);
        
        // 绘制失败标记（X）
        this.ctx.beginPath();
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;
        this.ctx.moveTo(10, y + 15);
        this.ctx.lineTo(30, y + 25);
        this.ctx.moveTo(30, y + 15);
        this.ctx.lineTo(10, y + 25);
        this.ctx.stroke();
    }
}