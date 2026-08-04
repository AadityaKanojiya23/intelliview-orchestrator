import { onCLS, onFCP, onINP, onLCP, onTTFB } from "web-vitals";
import { endpoints } from "./api";

async function sendMetric(metric) {
  console.log("Web Vital:", metric);

  try {
    await endpoints.reportWebVitals({
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      delta: metric.delta,
      id: metric.id,
      navigationType: metric.navigationType,
    });
  } catch (err) {
    console.error("Failed to send Web Vital:", err);
  }
}

export function initWebVitals() {
  onCLS(sendMetric);
  onFCP(sendMetric);
  onINP(sendMetric);
  onLCP(sendMetric);
  onTTFB(sendMetric);
}