"use client";

import { useEffect } from "react";

/**
 * Service Worker Registration Component
 * Registers the PWA service worker for offline caching and push notifications.
 * Part of v1.1.0 Mobile-Responsive Dashboard (PWA) feature.
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.log("[PWA] Service Worker registered:", registration.scope);

          // Check for updates periodically
          registration.addEventListener("updatefound", () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener("statechange", () => {
                if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
                  // New version available
                  console.log("[PWA] New version available");
                  dispatchEvent(new CustomEvent("sw-update-available"));
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error("[PWA] Service Worker registration failed:", error);
        });

      // Handle controller change (new SW activated)
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        console.log("[PWA] Controller changed, reloading...");
      });
    }
  }, []);

  return null;
}

/**
 * Hook to request push notification permission
 */
export function usePushNotifications() {
  const requestPermission = async (): Promise<boolean> => {
    if (!("Notification" in window)) {
      console.warn("[PWA] Push notifications not supported");
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === "granted";
  };

  const subscribeToPush = async (): Promise<PushSubscription | null> => {
    if (!("serviceWorker" in navigator)) {
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
      });
      return subscription;
    } catch (error) {
      console.error("[PWA] Push subscription failed:", error);
      return null;
    }
  };

  return { requestPermission, subscribeToPush };
}

/**
 * Hook to detect online/offline status
 */
export function useOnlineStatus() {
  const getOnlineStatus = () => {
    if (typeof navigator !== "undefined") {
      return navigator.onLine;
    }
    return true;
  };

  return getOnlineStatus();
}
