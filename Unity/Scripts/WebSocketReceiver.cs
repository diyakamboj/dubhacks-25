using UnityEngine;
using WebSocketSharp;
using System;

public class WebSocketReceiver : MonoBehaviour
{
    private WebSocket ws;
    public InstructionManager instructionManager;

    void Start()
    {
        ws = new WebSocket("ws://localhost:8765"); // change to your backend URL
        ws.OnMessage += OnMessageReceived;
        ws.Connect();
    }

    private void OnMessageReceived(object sender, MessageEventArgs e)
    {
        Debug.Log("Message from server: " + e.Data);

        // parse JSON
        EventData data = JsonUtility.FromJson<EventData>(e.Data);
        if (instructionManager != null)
            instructionManager.HandleEvent(data);
    }

    void OnDestroy()
    {
        ws.Close();
    }

    [Serializable]
    public class EventData
    {
        public string eventType;
        public float confidence;
        public string message;
    }
}
