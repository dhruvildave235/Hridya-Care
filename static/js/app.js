import { Utils } from './utils.js';
import { UI } from './ui.js';
import { Sensor } from './sensor.js';

let userData = {
  intenseActivity: false,
  city: "",
  aqi: 0,
  pm25: null,
  pm10: null,
  age: 0,
  baseline: 0,
  bpm: 0
};

async function fetchRealAQIByCity(city) {
  try {
    const res = await fetch(`/api/aqi?city=${encodeURIComponent(city)}`);
    const json = await res.json(); 

    console.log("Backend Response:", json); 

    if (!res.ok || json.error) {
        console.warn("AQI Error:", json.error);
        return null;
    }

    let finalAQI = json.aqi;
    const pm25 = json.pm25;

    if (pm25 !== null && (finalAQI < 20 || finalAQI === pm25)) {
        console.log("⚠️ AQI seems wrong (Value: " + finalAQI + "). Recalculating from PM2.5...");
        finalAQI = calculateUS_AQI(pm25);
    }

    return {
      aqi: finalAQI,
      pm25: pm25 || null,
      pm10: json.pm10 || null
    };

  } catch (err) {
    console.error("Failed to fetch AQI:", err);
    return null;
  }
}

function calculateUS_AQI(pm25) {
    if (pm25 == null || pm25 < 0) return 0;
    let c = parseFloat(pm25);
    
    if (c <= 12.0) return Math.round(((50 - 0) / (12.0 - 0)) * (c - 0) + 0);
    if (c <= 35.4) return Math.round(((100 - 51) / (35.4 - 12.1)) * (c - 12.1) + 51);
    if (c <= 55.4) return Math.round(((150 - 101) / (55.4 - 35.5)) * (c - 35.5) + 101);
    if (c <= 150.4) return Math.round(((200 - 151) / (150.4 - 55.5)) * (c - 55.5) + 151);
    if (c <= 250.4) return Math.round(((300 - 201) / (250.4 - 150.5)) * (c - 150.5) + 201);
    if (c <= 350.4) return Math.round(((400 - 301) / (350.4 - 250.5)) * (c - 250.5) + 301);
    return Math.round(((500 - 401) / (500.4 - 350.5)) * (c - 350.5) + 401);
}

document.addEventListener("DOMContentLoaded", () => {

  UI.showStep("step-1");

  if (
    localStorage.getItem("RESTORE_RESULT") === "1" &&
    window.location.pathname === "/report"
  ) {
    localStorage.removeItem("RESTORE_RESULT");

    const report = JSON.parse(localStorage.getItem("CARDIOSENSE_REPORT"));
    if (!report) return;

    fetchRealAQIByCity(report.city).then(aqiData => {
      if (!aqiData) return;

      report.aqi = aqiData.aqi;
      report.pm25 = aqiData.pm25;
      report.pm10 = aqiData.pm10;

      localStorage.setItem(
        "CARDIOSENSE_REPORT",
        JSON.stringify(report)
      );
    });
  }

  document.getElementById("btn-activity-yes").onclick = () => {
    userData.intenseActivity = true;
    UI.showStep("step-2");
  };

  document.getElementById("btn-activity-no").onclick = () => {
    userData.intenseActivity = false;
    UI.showStep("step-2");
  };

  document.getElementById("btn-city-next").onclick = async () => {
    const city = document.getElementById("input-city").value.trim();
    if (!city) return;

    const aqiData = await fetchRealAQIByCity(city);
    if (!aqiData) {
      alert("Unable to fetch AQI");
      return;
    }

    userData.city = city;
    userData.aqi = aqiData.aqi;
    userData.pm25 = aqiData.pm25;
    userData.pm10 = aqiData.pm10;

    console.log("✅ AQI STORED:", userData);
    UI.showStep("step-3");
  };

});

UI.showStep("step-1");

document.getElementById("btn-dashboard").onclick = () => {
    clearSession();
    window.location.href = "/";
};

document.getElementById("btn-back-to-activity").onclick = () => {
    UI.showStep("step-1");
};

document.getElementById("btn-back-to-location").onclick = () => {
    UI.showStep("step-2");
};

document.getElementById("btn-back-to-age").onclick = () => {
    Sensor.reset?.();
    UI.showStep("step-3");
};

const cityInput = document.getElementById("input-city");
const suggestionBox = document.getElementById("city-suggestions");

cityInput.addEventListener("input", () => {
    const value = cityInput.value.trim().toLowerCase();
    suggestionBox.innerHTML = "";

    if (!value) {
        suggestionBox.style.display = "none";
        return;
    }

    const matches = cities.filter(c =>
        c.toLowerCase().startsWith(value)
    );

    if (!matches.length) {
        suggestionBox.style.display = "none";
        return;
    }

    matches.forEach(city => {
        const li = document.createElement("li");
        li.textContent = city;
        li.onclick = () => {
            cityInput.value = city;
            suggestionBox.innerHTML = "";
            suggestionBox.style.display = "none";
        };
        suggestionBox.appendChild(li);
    });

    suggestionBox.style.display = "block";
});

document.getElementById('btn-activity-yes').onclick = () => {
    userData.intenseActivity = true;
    UI.showStep('step-2');
};

document.getElementById('btn-activity-no').onclick = () => {
    userData.intenseActivity = false;
    UI.showStep('step-2');
};

document.getElementById('btn-city-next').onclick = async () => {
  const city = cityInput.value.trim();
  if (!city) return;

  const aqiData = await fetchRealAQIByCity(city);
  if (!aqiData) {
    alert("Unable to fetch AQI");
    return;
  }

  userData.city = city;
  userData.aqi = aqiData.aqi;
  userData.pm25 = aqiData.pm25;
  userData.pm10 = aqiData.pm10;

  console.log("✅ Stored AQI:", userData);

  UI.showStep("step-3");
};

document.getElementById('btn-age-next').onclick = () => {
    const age = parseInt(document.getElementById('input-age').value);
    if (!age) return;

    userData.age = age;
    userData.baseline = Utils.getBaselineHR(age);
    UI.showStep('step-monitor');
};

document.getElementById('btn-start-measure').onclick = () => {
    UI.showStep('step-monitor');
    Sensor.init(bpm => {
        userData.bpm = bpm;
        processResults();
    });
};

document.getElementById("btn-view-report").onclick = () => {
    localStorage.setItem("RESTORE_RESULT", "1");
    window.location.href = "/report";
};

document.getElementById("btn-restart").onclick = () => {
    localStorage.removeItem("CARDIOSENSE_REPORT");
    window.location.href = "/heart-rate";
};

function processResults() {
  UI.showStep("step-5");

  const deltaHR = Math.max(0, userData.bpm - userData.baseline);
  const impactPercent = Math.min(100, deltaHR * 5);

  const impactCategory =
    impactPercent < 10 ? "Minimal Influence" :
    impactPercent < 30 ? "Mild Contribution" :
    impactPercent < 50 ? "Moderate Impact" :
    "High Strain";

  const message =
    impactCategory === "Minimal Influence"
      ? "Your heart rate is within expected range."
      : "Environmental factors may be affecting your heart rate.";

  UI.updateReport(
    {
      age: userData.age,
      city: userData.city,
      bpm: userData.bpm,
      aqi: userData.aqi,
      pm25: userData.pm25,
      pm10: userData.pm10,
      impactCategory,
      message,
      timestamp: new Date().toISOString()
    },
    impactPercent,
    impactCategory,
    "#10b981",
    message
  );
}

const activityState = userData.intenseActivity ? "active" : "resting";

const explanation = explainHeartRate({
    bpm: userData.bpm,
    age: userData.age,
    activity: activityState,
    aqi: userData.aqi
});

const confidence = getConfidenceScore({
    bpm: userData.bpm,
    age: userData.age,
    activity: activityState,
    aqi: userData.aqi
});

const explainBox = document.getElementById("hr-explanation");
const resMsg = document.getElementById("res-msg");

if (explainBox && explanation) {
    document.getElementById("hr-explanation-text").innerText = explanation;
    document.getElementById("hr-confidence").innerText =
        `Confidence: ${confidence}%`;
    explainBox.style.display = "block";
    if (resMsg) resMsg.style.display = "none";
}

fetch("/api/heart-rate/last-7")
    .then(res => res.json())
    .then(history => {
        const box = document.getElementById("personal-baseline-box");
        if (!box || !history || history.length === 0) return;

        const insights = Utils.generatePersonalInsights(history);
        box.innerHTML = `
            <div>📊 ${insights.deviationText}</div>
            <div style="margin-top:6px;">🧠 ${insights.stabilityText}</div>
        `;
        box.style.display = "block";
    });

function clearSession() {
    localStorage.removeItem("RESTORE_RESULT");
}

function getExpectedBPM(age) {
    if (age < 25) return 72;
    if (age < 40) return 70;
    if (age < 55) return 73;
    return 75;
}

function explainHeartRate({ bpm, age, activity, aqi }) {
    if (activity === "active") {
        return "Your heart rate is elevated primarily due to recent physical activity.";
    }

    const expected =
        getExpectedBPM(age) +
        getAQIImpact(aqi).bpm +
        getTimeImpact().bpm;

    if (bpm > expected + 6) {
        return "Environmental and situational factors may be contributing to your elevated heart rate.";
    }

    return "Your heart rate aligns with expected levels for current conditions.";
}

function getConfidenceScore({ bpm, age, activity, aqi }) {
  let score = 50;

  if (aqi > 300) score += 25;
  else if (aqi > 200) score += 20;
  else if (aqi > 150) score += 15;
  else if (aqi > 100) score += 10;
  else score += 5;

  score += activity === "active" ? 15 : 10;
  score += Math.abs(bpm - getExpectedBPM(age)) >= 8 ? 10 : 5;

  return Math.min(95, score);
}

function getAQIImpact(aqi) {
  if (aqi <= 50) return { bpm: 0 };
  if (aqi <= 100) return { bpm: 2 };
  if (aqi <= 150) return { bpm: 5 };
  if (aqi <= 200) return { bpm: 10 };
  if (aqi <= 300) return { bpm: 15 };
  return { bpm: 20 };
}

function getTimeImpact() {
    const h = new Date().getHours();
    if (h >= 6 && h < 12) return { bpm: 0 };
    if (h >= 12 && h < 17) return { bpm: 3 };
    if (h >= 17 && h < 22) return { bpm: 6 };
    return { bpm: 4 };
}

function getAQILabel(aqi) {
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy (Sensitive)";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unhealthy";
  return "Hazardous";
}

function getAQIColor(aqi) {
  if (aqi <= 50) return "#22c55e";
  if (aqi <= 100) return "#eab308";
  if (aqi <= 150) return "#f97316";
  if (aqi <= 200) return "#ef4444";
  if (aqi <= 300) return "#7c2d12";
  return "#3b0764";
}

const cities = [
  "Ahmedabad","Surat","Vadodara","Rajkot","Gandhinagar",
  "Mumbai","Pune","Nagpur","Nashik","Thane",
  "Delhi","Noida","Ghaziabad","Faridabad","Gurugram",
  "Bengaluru","Chennai","Hyderabad","Kolkata",
  "Jaipur","Udaipur","Jodhpur","Ajmer","Kota","Bikaner",
  "Indore","Bhopal","Gwalior","Jabalpur","Ujjain","Sagar",
  "Lucknow","Kanpur","Varanasi","Prayagraj","Agra","Meerut",
  "Bareilly","Aligarh","Moradabad","Saharanpur",
  "Bhavnagar","Jamnagar","Junagadh","Porbandar","Anand",
  "Nadiad","Navsari","Valsad","Vapi","Morbi",
  "Aurangabad","Solapur","Kolhapur","Sangli","Satara",
  "Amravati","Akola","Latur","Nanded","Parbhani",
  "Coimbatore","Madurai","Tiruchirappalli","Salem","Erode",
  "Vellore","Tirunelveli","Thoothukudi",
  "Kochi","Thiruvananthapuram","Kozhikode","Thrissur",
  "Mysuru","Mangaluru","Hubballi","Belagavi",
  "Vijayawada","Guntur","Nellore","Tirupati","Kakinada",
  "Bhubaneswar","Cuttack","Rourkela",
  "Patna","Gaya","Muzaffarpur","Bhagalpur",
  "Ranchi","Dhanbad","Jamshedpur",
  "Siliguri","Asansol","Durgapur",
  "Chandigarh","Dehradun","Haridwar","Roorkee",
  "Shimla","Solan","Una",
  "Jammu","Srinagar","Anantnag",
  "Amritsar","Ludhiana","Jalandhar","Patiala","Bathinda",
  "Guwahati","Silchar","Dibrugarh",
  "Imphal","Agartala","Aizawl","Kohima","Dimapur",
  "Shillong","Itanagar",
  "Raipur","Bilaspur","Durg",
  "Panaji","Margao",
  "Port Blair"
];
