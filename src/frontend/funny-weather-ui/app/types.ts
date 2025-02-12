export interface WeatherJokeResponse {
    location: string;
    timestamp: string;
    weather: {
        temperature_celsius: number;
        wind_speed: number;
        cloud_cover: number;
        visibility: number;
        humidity: number;
    };
    joke: {
        emoji: string;
        weather_status: string;
        jokes: string[];
    };
} 