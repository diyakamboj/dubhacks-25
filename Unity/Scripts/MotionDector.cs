using UnityEngine;
using System.Collections;

public class MotionDetector : MonoBehaviour
{
    private bool isUnresponsive = false;
    private float motionTimer = 0f;
    private Vector3 lastPosition;

    void Start()
    {
        lastPosition = transform.position;
    }

    void Update()
    {
        // TEMP: press 'M' to simulate detection
        if (Input.GetKeyDown(KeyCode.M))
        {
            ToggleUnresponsive();
        }

        if (!isUnresponsive)
        {
            float movement = Vector3.Distance(transform.position, lastPosition);
            if (movement < 0.01f)
            {
                motionTimer += Time.deltaTime;
                if (motionTimer > 3f)
                {
                    Debug.Log("⚠️ No movement detected. Checking responsiveness...");
                    // TODO: trigger CV signal or AR alert
                    motionTimer = 0f;
                }
            }
            else
            {
                motionTimer = 0f;
            }

            lastPosition = transform.position;
        }
    }

    private void ToggleUnresponsive()
    {
        isUnresponsive = !isUnresponsive;
        motionTimer = 0f;
        Debug.Log(isUnresponsive ? "Unresponsiveness simulation started." : "Unresponsiveness simulation stopped.");
    }
}
