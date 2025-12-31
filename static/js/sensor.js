import { CONFIG } from './config.js';
import { UI } from './ui.js';

let state = 'IDLE';
let ctx, canvas;
let buffer = [];
let beatTimes = [];
let startTime = 0;
let stabilizeStart = 0;
let dynamicMean = 0;
let isAboveMean = false;
let animationFrameId;
let mediaStream = null; 
let scrollIndex = 0;

export const Sensor = {
    async init(onComplete, onRetry) {
        const btn = document.getElementById('btn-start-measure');
        btn.innerText = "ACCESSING CAMERA..."; 
        btn.disabled = true;
        document.getElementById('pre-start-text').style.display = "none";
        document.getElementById('measuring-ui').style.display = "block";

        updateMeasuringUI(0, "stabilizing");
       
        canvas = document.getElementById('graph');
        canvas.width = 360;
        canvas.height = 120;

        ctx = canvas.getContext('2d');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment', width: {ideal:128}, height: {ideal:128}, frameRate: {ideal:30} }
            });
            mediaStream = stream;
            
            const video = document.getElementById('video');
            video.srcObject = stream; 
            video.setAttribute('playsinline', ''); 
            video.play();
            
            const track = stream.getVideoTracks()[0];
            try { await track.applyConstraints({ advanced: [{ torch: true }] }); } catch(e){}
            
            this.enterState('WAITING', onComplete);
            this.loop(onComplete);
        } catch(e) { 
            UI.updateMessage("Camera Denied", "var(--primary)"); 
            btn.innerText = "RETRY"; 
            btn.disabled = false; 
            btn.onclick = onRetry;
        }
    },

    loop(onComplete) {
        if (state === 'FINISHED') return;

        const video = document.getElementById('video');
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            const tCtx = document.createElement('canvas').getContext('2d');
            tCtx.drawImage(video, 0, 0, 1, 1);
            const px = tCtx.getImageData(0,0,1,1).data;
            const r = px[0]; const g = px[1]; const b = px[2];
            
            const isFinger = (r > 60) && (r > (g + b) * 0.6); 
            const now = Date.now();

            if (state === 'WAITING') {
                if (isFinger) { 
                    this.enterState('STABILIZING'); 
                    stabilizeStart = now; 
                }
            } else if (state === 'STABILIZING') {
                if (!isFinger) this.enterState('WAITING');
                else {
                    const elapsed = now - stabilizeStart;
                    if(elapsed >= CONFIG.STABILIZE_MS) this.enterState('MEASURING');
                    else {
                        const rem = Math.ceil((CONFIG.STABILIZE_MS - elapsed)/1000);
                        UI.updateCountdown(rem > 0 ? rem : "GO");
                        UI.setRingProgress(
                            elapsed / CONFIG.STABILIZE_MS,
                            "var(--warning)",
                            CONFIG.RING_LENGTH
                        );

                        const percent = Math.min(
                            Math.round((elapsed / CONFIG.STABILIZE_MS) * 30),
                            30
                        );
                        updateMeasuringUI(percent, "stabilizing");
                    }
                }
            } else if (state === 'MEASURING') {
                if (!isFinger) this.enterState('WAITING');
                else {
                    const elapsed = (now - startTime) / 1000;
                    if(elapsed >= CONFIG.DURATION) this.enterState('RESULT', onComplete);
                    else {
                        UI.setRingProgress(
                            elapsed / CONFIG.DURATION,
                            "var(--primary)",
                            CONFIG.RING_LENGTH
                        );
                        UI.updateCountdown(Math.ceil(CONFIG.DURATION - elapsed));

                        const percent = 30 + Math.round((elapsed / CONFIG.DURATION) * 60);
                        updateMeasuringUI(Math.min(percent, 90), "measuring");

                        const val = -r; 
                        buffer.push(val); 
                        if(buffer.length > 100) buffer.shift();

                        this.drawGraph(); 
                        this.detectBeat(val, now);
                    }
                }
            }
        }
        animationFrameId = requestAnimationFrame(() => this.loop(onComplete));
    },

    enterState(newState, onComplete) {
        state = newState;
        UI.updateOverlay(false);
        UI.setCamBorder("rgba(255,255,255,0.1)");
        UI.setLiveBadge('0');

        if (newState === 'WAITING') {

            document.body.classList.remove("focus-mode");

            document.querySelector('.graph-container')
                .classList.remove('full-width');

            UI.updateMessage(
                "Gently cover Camera & Flash. Do not press hard, or readings will be high.",
                "var(--text-muted)"
            );

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            buffer = [];
            dynamicMean = 0;
        }

        else if (newState === 'STABILIZING') {

            document.body.classList.add("focus-mode");

            UI.updateMessage("Hold still...", "var(--warning)");
            UI.updateOverlay(true, "HOLD");
            UI.setCamBorder("var(--warning)");
        }

        else if (newState === 'MEASURING') {

            document.body.classList.add("focus-mode");

            startTime = Date.now();
            beatTimes = [];
            buffer = [];

            document.querySelector('.graph-container')
                .classList.add('full-width');

            UI.updateMessage("Measuring...", "var(--primary)");
            UI.setLiveBadge('1');
            UI.updateOverlay(true, "SEC");
            UI.setCamBorder("var(--primary)");
        }

        else if (newState === 'RESULT') {

            document.body.classList.remove("focus-mode");

            document.querySelector('.graph-container')
                .classList.remove('full-width');

            this.finishExam(onComplete);
        }
    },

    detectBeat(val, time) {
        if (dynamicMean === 0) { dynamicMean = val; return; }
        dynamicMean = (dynamicMean * 0.95) + (val * 0.05);
        if (!isAboveMean && val > (dynamicMean + 0.4)) {
            isAboveMean = true;
            if (time - (beatTimes[beatTimes.length - 1]||0) > 300) { 
                beatTimes.push(time); 
                UI.triggerPulseAnim(); 
            }
        } else if (isAboveMean && val < (dynamicMean - 0.4)) { isAboveMean = false; }
    },

    drawGraph() {
        ctx.clearRect(0,0,canvas.width,canvas.height); 
        if(buffer.length<2) return;
        
        let min=Math.min(...buffer), max=Math.max(...buffer), range=max-min||1;
        let w=canvas.width, h=canvas.height, p=10;
        
        let g=ctx.createLinearGradient(0,0,w,0); 
        g.addColorStop(0,"rgba(244,63,94,0.1)"); 
        g.addColorStop(1,"rgba(244,63,94,1)");
        
        ctx.strokeStyle=g; ctx.lineWidth=3; ctx.lineCap='round'; ctx.lineJoin='round'; 
        ctx.beginPath();
        for(let i=0; i<buffer.length; i++) {
            let x=(i/(buffer.length-1))*w; 
            let y=h-(((buffer[i]-min)/range)*(h-2*p)+p);
            i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
        }
        ctx.stroke();
    },

    finishExam(onComplete) {
        cancelAnimationFrame(animationFrameId);
        let bpm = 0;
        if (beatTimes.length >= 3) {
            let ints = [];
            for(let i=1; i<beatTimes.length; i++) {
                let interval = beatTimes[i] - beatTimes[i-1];
                if (interval > 300 && interval < 1500) ints.push(interval);
            }
            if (ints.length > 0) {
                ints.sort((a,b)=>a-b);
                bpm = Math.round(60000/ints[Math.floor(ints.length/2)]);
            }
        }

        this.stopCamera();

        if (bpm > 40 && bpm < 220) {
            UI.setRingProgress(1, "var(--success)", CONFIG.RING_LENGTH);
            UI.updateMessage("Calculation Complete", "var(--text-muted)");

            const reportData = {
                name: "User",
                age: document.getElementById("input-age")?.value || "--",
                city: document.getElementById("input-city")?.value || "--",
                bpm: bpm,
                aqi: window.currentAQI || "--",
                impactCategory: bpm > 100 ? "High" : "Normal",
                message:
                    bpm > 100
                      ? "Your heart rate is elevated. Please rest."
                      : "Your heart rate is within a healthy range.",
                timestamp: new Date().toLocaleString("en-IN", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit"
                })
            };

            localStorage.setItem(
                "CARDIOSENSE_REPORT",
                JSON.stringify(reportData)
            );

            fetch('/save-heart-rate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bpm: bpm,
                    aqi: window.currentAQI || null,
                    stress: "Normal",
                    impact: "Low"
                })
            });

            onComplete(bpm);
        }

        else {
            UI.setRingProgress(1, "var(--primary)", CONFIG.RING_LENGTH);
            UI.setBPM("Err");
            UI.updateMessage("Signal Weak. Retry.", "var(--primary)");
            
            setTimeout(() => { 
                const btn = document.getElementById('btn-start-measure');
                btn.style.display = "block"; 
                btn.innerText = "RETRY"; 
                btn.disabled = false;
                btn.onclick = () => { 
                    this.reset();
                    this.init(onComplete, () => this.init(onComplete)); 
                };
            }, 1500);
        }
    },
    
    stopCamera() {
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => {
                track.stop();
            });
            mediaStream = null;
            
            const video = document.getElementById('video');
            if (video) {
                video.srcObject = null;
            }
        }
    },
    
    reset() {
        state = 'IDLE';
        cancelAnimationFrame(animationFrameId);
        this.stopCamera(); 
    }
};

function updateMeasuringUI(percent, phase) {
    document.getElementById('measure-percent').innerText = `${percent}%`;

    if (phase === "stabilizing") {
        document.getElementById('line-1').innerText = "Hold finger steady";
        document.getElementById('line-2').innerText = "Stabilizing signal";
        document.getElementById('line-3').innerText = "Almost ready…";
    }

    if (phase === "measuring") {
        document.getElementById('line-1').innerText = "Measuring pulse";
        document.getElementById('line-2').innerText = "Analyzing blood flow";
        document.getElementById('line-3').innerText = "Please stay still";
    }

    if (phase === "final") {
        document.getElementById('line-1').innerText = "Finalizing result";
        document.getElementById('line-2').innerText = "Calculating BPM";
        document.getElementById('line-3').innerText = "Almost done";
    }
}
