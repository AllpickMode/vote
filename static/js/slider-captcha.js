
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
        this.isDragging = false;
        this.destroyed = false;
        this.init();
        
        // 添加清理方法
        this.destroy = () => {
            this.destroyed = true;
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
        this.createCaptchaImage();
        this.createSlider();
        this.bindEvents();
        await this.refresh();
    }

    createCaptchaImage() {
        // 创建图片容器
        this.imageContainer = document.createElement('div');
        this.imageContainer.className = 'slider-captcha-image-container';
        this.imageContainer.style.width = this.options.width + 'px';
        this.imageContainer.style.height = this.options.height + 'px';
        this.imageContainer.style.position = 'relative';
        this.imageContainer.style.overflow = 'hidden';
        
        // 创建验证码图片
        this.captchaImage = document.createElement('img');
        this.captchaImage.className = 'slider-captcha-image';
        this.captchaImage.style.width = '100%';
        this.captchaImage.style.height = '100%';
        this.captchaImage.style.display = 'block';
        
        this.imageContainer.appendChild(this.captchaImage);
        this.element.appendChild(this.imageContainer);
    }

    createSlider() {
        // 创建滑块容器
        this.sliderContainer = document.createElement('div');
        this.sliderContainer.className = 'slider-captcha-container';
        this.sliderContainer.style.position = 'relative';
        this.sliderContainer.style.width = this.options.width + 'px';
        
        // 创建滑块轨道
        this.sliderTrack = document.createElement('div');
        this.sliderTrack.className = 'slider-captcha-track';
        
        // 创建滑块
        this.slider = document.createElement('div');
        this.slider.className = 'slider-captcha-handle';
        this.slider.style.width = this.options.sliderWidth + 'px';
        this.slider.style.height = this.options.sliderHeight + 'px';
        
        // 组装滑块组件
        this.sliderTrack.appendChild(this.slider);
        this.sliderContainer.appendChild(this.sliderTrack);
        this.element.appendChild(this.sliderContainer);
    }

    async getCaptchaData() {
        try {
            const response = await fetch('/api/captcha/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    position: this.currentPosition,
                    token: this.currentToken
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
        this.currentPosition = 0;
        this.currentToken = null;

        const moveHandler = (e) => {
            if (!this.isDragging || this.destroyed) return;
            e.preventDefault();
            
            const touch = e.type === 'touchmove' ? e.touches[0] : e;
            let moveX = touch.clientX - startX;
            moveX = Math.max(0, Math.min(moveX, this.options.width - this.options.sliderWidth));
            
            this.slider.style.transform = `translate3d(${moveX}px, 0, 0)`;
            this.currentPosition = moveX;
        };

        const upHandler = async () => {
            if (!this.isDragging || this.destroyed) return;
            this.stopDragging();
            
            document.removeEventListener('mousemove', moveHandler);
            document.removeEventListener('touchmove', moveHandler);
            document.removeEventListener('mouseup', upHandler);
            document.removeEventListener('touchend', upHandler);

            try {
                const result = await this.getCaptchaData();
                if (this.destroyed) return;

                if (result.success) {
                    this.sliderTrack.classList.add('success');
                    document.getElementById('verificationToken').value = result.verification_token;
                    this.options.onSuccess();
                } else {
                    this.sliderTrack.classList.add('fail');
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
            
            document.addEventListener('mousemove', moveHandler);
            document.addEventListener('touchmove', moveHandler);
            document.addEventListener('mouseup', upHandler);
            document.addEventListener('touchend', upHandler);
        };

        this.downHandler = downHandler;
        this.slider.addEventListener('mousedown', this.downHandler);
        this.slider.addEventListener('touchstart', this.downHandler);
    }

    async refresh() {
        try {
            // 获取新的验证码图片
            const timestamp = new Date().getTime(); // 防止缓存
            this.captchaImage.src = `/api/captcha/generate?t=${timestamp}`;
            
            // 重置滑块位置
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
        this.currentPosition = 0;
        setTimeout(() => {
            this.slider.style.transition = '';
        }, 300);
    }
}