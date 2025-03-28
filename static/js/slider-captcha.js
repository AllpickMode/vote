
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
        this.init();
    }

    init() {
        this.createCanvas();
        this.createSlider();
        this.bindEvents();
        this.refresh();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
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
        this.sliderText = document.createElement('span');
        this.sliderText.textContent = '向右滑动验证';
        this.sliderTrack.appendChild(this.sliderText);
        this.sliderTrack.appendChild(this.slider);
        this.element.appendChild(this.sliderTrack);
    }

    bindEvents() {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;

        const moveHandler = (e) => {
            if (!isDragging) return;
            
            const touch = e.type === 'touchmove' ? e.touches[0] : e;
            let moveX = touch.clientX - startX;
            moveX = Math.max(0, Math.min(moveX, this.options.width - this.options.sliderWidth));
            
            this.slider.style.left = `${moveX}px`;
            currentX = moveX;
            
            // 重绘Canvas
            this.ctx.clearRect(0, 0, this.options.width, this.options.height);
            this.drawBackground();
            
            // 绘制目标位置的方块（半透明）
            const y = this.options.height / 2 - this.options.sliderHeight / 2;
            this.ctx.fillStyle = '#75b83e80';
            this.ctx.fillRect(this.targetPos, y, this.options.sliderWidth, this.options.sliderHeight);
            
            // 绘制当前滑块位置的方块
            this.ctx.fillStyle = '#75b83e';
            this.ctx.fillRect(moveX, y, this.options.sliderWidth, this.options.sliderHeight);
        };

        const upHandler = () => {
            if (!isDragging) return;
            isDragging = false;
            
            document.removeEventListener('mousemove', moveHandler);
            document.removeEventListener('touchmove', moveHandler);
            document.removeEventListener('mouseup', upHandler);
            document.removeEventListener('touchend', upHandler);

            const accuracy = 10;
            if (Math.abs(currentX - this.targetPos) <= accuracy) {
                this.sliderTrack.classList.add('success');
                this.options.onSuccess();
            } else {
                this.sliderTrack.classList.add('fail');
                setTimeout(() => {
                    this.reset();
                    this.refresh();
                }, 1000);
                this.options.onFail();
            }
        };

        const downHandler = (e) => {
            isDragging = true;
            const touch = e.type === 'touchstart' ? e.touches[0] : e;
            startX = touch.clientX - this.slider.offsetLeft;
            
            document.addEventListener('mousemove', moveHandler);
            document.addEventListener('touchmove', moveHandler);
            document.addEventListener('mouseup', upHandler);
            document.addEventListener('touchend', upHandler);
        };

        this.slider.addEventListener('mousedown', downHandler);
        this.slider.addEventListener('touchstart', downHandler);
    }

    refresh() {
        this.ctx.clearRect(0, 0, this.options.width, this.options.height);
        this.drawBackground();
        this.targetPos = Math.random() * (this.options.width - this.options.sliderWidth * 2) + this.options.sliderWidth;
        this.drawPuzzle();
        this.reset();
        this.options.onRefresh();
    }

    reset() {
        this.slider.style.left = '0px';
        this.sliderTrack.classList.remove('success', 'fail');
    }

    drawBackground() {
        this.ctx.fillStyle = '#e8e8e8';
        this.ctx.fillRect(0, 0, this.options.width, this.options.height);
    }

    drawPuzzle() {
        const y = this.options.height / 2 - this.options.sliderHeight / 2;
        
        // Draw target area
        this.ctx.fillStyle = '#75b83e';
        this.ctx.fillRect(this.targetPos, y, this.options.sliderWidth, this.options.sliderHeight);
        
        // Draw initial slider position
        this.ctx.fillStyle = '#75b83e80';
        this.ctx.fillRect(0, y, this.options.sliderWidth, this.options.sliderHeight);
    }
}