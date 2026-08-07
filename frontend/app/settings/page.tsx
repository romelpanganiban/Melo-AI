"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  getSettings,
  updateSettings,
} from "@/lib/api";

export default function SettingsPage() {
  const [model, setModel] =
    useState("");

  const [provider, setProvider] =
    useState("");

  const [
    temperature,
    setTemperature,
  ] = useState(0.7);

  useEffect(() => {
    async function loadSettings() {
      const settings =
        await getSettings();

      setModel(
        settings.model
      );

      setProvider(
        settings.provider
      );

      setTemperature(
        settings.temperature
      );
    }

    loadSettings();
  }, []);

  async function handleSave() {
    await updateSettings({
      model,
      provider,
      temperature,
    });

    alert(
      "Settings saved!"
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-8 space-y-6">

      <h1 className="text-3xl font-bold">
        Settings
      </h1>

      <div>
        <label className="block mb-2">
          Model
        </label>

        <input
          value={model}
          onChange={(e) =>
            setModel(
              e.target.value
            )
          }
          className="border rounded p-2 w-full"
        />
      </div>

      <div>
        <label className="block mb-2">
          Provider
        </label>

        <input
          value={provider}
          onChange={(e) =>
            setProvider(
              e.target.value
            )
          }
          className="border rounded p-2 w-full"
        />
      </div>

      <div>
        <label className="block mb-2">
          Temperature
        </label>

        <input
          type="number"
          step="0.1"
          min="0"
          max="2"
          value={temperature}
          onChange={(e) =>
            setTemperature(
              Number(
                e.target.value
              )
            )
          }
          className="border rounded p-2 w-full"
        />
      </div>

      <button
        onClick={handleSave}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Save Settings
      </button>

    </div>
  );
}