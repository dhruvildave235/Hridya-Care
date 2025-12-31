export const Utils = {
    getBaselineHR(age) {
        if (age >= 10 && age <= 12) return 85;
        if (age >= 13 && age <= 15) return 80;
        if (age >= 16 && age <= 17) return 75;
        if (age >= 18 && age <= 25) return 70;
        if (age >= 26 && age <= 35) return 72;
        if (age >= 36 && age <= 45) return 74;
        if (age >= 46 && age <= 55) return 76;
        if (age >= 56 && age <= 65) return 78;
        if (age > 65) return 80;
        return 72;
    },

    getAQIWeight(openWeatherAQI) {
        const aqi = Number(openWeatherAQI);
        switch (aqi) {
            case 1: return 0.0;
            case 2: return 0.15;
            case 3: return 0.35;
            case 4: return 0.65;
            case 5: return 0.90;
            default: return 0.0;
        }
    },

    fetchSimulatedAQI(city) {
        let hash = 0;
        for (let i = 0; i < city.length; i++) {
            hash = city.charCodeAt(i) + ((hash << 5) - hash);
        }
        const result = Math.abs(hash % 350);
        return result === 0 ? 55 : result;
    },

    getFinalReport() {
        if (!window.__CARDIOSENSE_REPORT__) {
            console.warn("No report data available yet");
            return null;
        }
        return window.__CARDIOSENSE_REPORT__;
    },

    generatePDF() {
        const report = this.getFinalReport();
        if (!report) {
            alert("Report data not ready yet");
            return;
        }

        const element = document.getElementById("pdf-report");
        if (!element) {
            alert("PDF template not found");
            return;
        }

        document.getElementById("pdf-name").innerText = report.name;
        document.getElementById("pdf-age").innerText = report.age;
        document.getElementById("pdf-city").innerText = report.city;
        document.getElementById("pdf-bpm").innerText = report.bpm;
        document.getElementById("pdf-aqi").innerText = report.aqi;
        document.getElementById("pdf-impact").innerText = report.impactCategory;
        document.getElementById("pdf-impact-percent").innerText = report.impactPercent + "%";
        document.getElementById("pdf-message").innerText = report.message;
        document.getElementById("pdf-time").innerText = report.timestamp;

        html2pdf().set({
            margin: 0.5,
            filename: "CardioSense_Health_Report.pdf",
            image: { type: "jpeg", quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: "in", format: "a4", orientation: "portrait" }
        }).from(element).save();
    },

    shareOnWhatsApp(phone, pdfLink) {
        const report = this.getFinalReport();
        if (!report) {
            alert("Report data not ready");
            return;
        }

        const message = `
HridyaCare Health Report ❤️

Heart Rate: ${report.bpm} BPM
AQI: ${report.aqi}
Impact: ${report.impactCategory}

Download PDF:
${pdfLink}
        `;

        window.open(
            `https://wa.me/${phone}?text=${encodeURIComponent(message)}`,
            "_blank"
        );
    },

    calculatePersonalAverage(history) {
        const values = history.map(h => h.bpm);
        return values.reduce((a, b) => a + b, 0) / values.length;
    },

    calculateDeviationPercent(latest, avg) {
        return Math.round(((latest - avg) / avg) * 100);
    },

    calculateStabilityScore(history) {
        const avg = this.calculatePersonalAverage(history);
        const variance =
            history.reduce((sum, h) => sum + Math.pow(h.bpm - avg, 2), 0) / history.length;
        return Math.max(0, Math.min(100, Math.round(100 - Math.sqrt(variance) * 5)));
    },

    generatePersonalInsights(history) {
        if (!history || history.length < 3) {
            return {
                deviationText: "Not enough previous readings to establish your personal baseline yet.",
                stabilityText: "Heart rate stability will be available after a few more sessions."
            };
        }

        const avg = this.calculatePersonalAverage(history);
        const latest = history[history.length - 1].bpm;
        const deviation = this.calculateDeviationPercent(latest, avg);
        const stability = this.calculateStabilityScore(history);

        return {
            deviationText:
                deviation > 0
                    ? `Today’s heart rate is ${deviation}% above your personal average.`
                    : `Today’s heart rate is ${Math.abs(deviation)}% below your personal average.`,
            stabilityText:
                stability >= 80
                    ? "Your heart rate pattern has been stable over recent sessions."
                    : stability >= 60
                        ? "Your heart rate stability has slightly reduced recently."
                        : "Your heart rate stability has reduced over the last few days.",
            stability
        };
    }
};
