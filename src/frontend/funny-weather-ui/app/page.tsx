'use client';

import { useEffect, useState } from "react";
import type { WeatherJokeResponse } from "./types";

export default function Home() {
  const [weatherData, setWeatherData] = useState<WeatherJokeResponse | null>(null);
  const [currentJokeIndex, setCurrentJokeIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWeatherData();
  }, []);

  const fetchWeatherData = async () => {
    try {
      const response = await fetch('https://cpetrstalc.execute-api.ap-southeast-2.amazonaws.com/prod/weather');
      if (!response.ok) throw new Error('Failed to fetch weather data');
      const data = await response.json();
      setWeatherData(data);
      setIsLoading(false);
    } catch (err) {
      console.error('Weather fetch error:', err);
      setError('Failed to load weather data');
      setIsLoading(false);
    }
  };

  const handleClick = () => {
    if (weatherData) {
      setCurrentJokeIndex((prevIndex) =>
        (prevIndex + 1) % weatherData.joke.jokes.length
      );
    }
  };

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
        <p className="text-red-500 dark:text-red-400">{error}</p>
      </div>
    </div>
  );

  if (!weatherData) return null;

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-8 cursor-pointer transition-colors duration-300 hover:bg-gray-50 dark:hover:bg-gray-900/50"
      onClick={handleClick}
    >
      <div className="text-8xl mb-4">
        {weatherData.joke.emoji}
      </div>

      <h1 className="text-3xl font-bold mb-8 text-center bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
        {weatherData.joke.weather_status}
      </h1>

      <div className="flex gap-6 mb-12 text-sm text-gray-600 dark:text-gray-400">
        <div className="flex flex-col items-center bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
          <span className="font-semibold mb-1">{weatherData.weather.temperature_celsius.toFixed(1)}°C</span>
          <span className="text-xs">Temperature</span>
        </div>
        <div className="flex flex-col items-center bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
          <span className="font-semibold mb-1">{weatherData.weather.wind_speed.toFixed(1)} m/s</span>
          <span className="text-xs">Wind Speed</span>
        </div>
        <div className="flex flex-col items-center bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
          <span className="font-semibold mb-1">{weatherData.weather.humidity.toFixed(1)}%</span>
          <span className="text-xs">Humidity</span>
        </div>
      </div>

      <div className="max-w-2xl">
        <div className="text-xl text-center px-8 py-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg transform transition-transform hover:scale-105">
          {weatherData.joke.jokes[currentJokeIndex].split('?').map((part, index, array) => (
            array.length > 1 && index < array.length - 1 ? (
              <span key={index}>
                {part}?<br />
              </span>
            ) : (
              <span key={index}>{part}</span>
            )
          ))}
        </div>
      </div>

      <div className="mt-12 text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
        <span className="animate-pulse">👆</span>
        Click anywhere for another joke!
      </div>
    </div>
  );
}
