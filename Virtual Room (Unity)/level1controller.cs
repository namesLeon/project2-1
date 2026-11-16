using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System;

public class level1controller : MonoBehaviour
{
    [Header("Physical Screen Setup (in meters)")]
    [Tooltip("Physical width of your monitor in meters (measure it!)")]
    public float screenWidth = 0.52f; // ~24 inch monitor width
    
    [Tooltip("Physical height of your monitor in meters")]
    public float screenHeight = 0.29f; // ~24 inch monitor height
    
    [Tooltip("Typical distance from your eyes to screen in meters")]
    public float viewingDistance = 0.6f; // 60 cm
    
    [Header("Virtual World Setup")]
    [Tooltip("How deep is your virtual scene? (units)")]
    public float virtualWorldDepth = 10f;
    
    [Tooltip("Width of the virtual viewing area at the screen plane")]
    public float virtualWorldWidth = 11.23937f;
    
    [Tooltip("Height of the virtual viewing area at the screen plane")]
    public float virtualWorldHeight = 5.894882f;
    
    [Header("Calibration")]
    [Tooltip("Fine-tune the effect intensity (1.0 = geometrically correct)")]
    public float parallaxIntensity = 1.0f;
    
    [Tooltip("Smooth camera movement speed")]
    public float smoothSpeed = 5f;
    
    [Header("UDP Settings")]
    public int port = 5052;
    
    // Calculated scales
    private float horizontalScale;
    private float verticalScale;
    private float depthScale;
    
    // Smoothed values
    private float smoothedX = 0f;
    private float smoothedY = 0f;
    private float smoothedZ = 0f;
    
    [Header("Smoothing")]
    [Tooltip("Higher = smoother but more lag (0.1-0.3 recommended)")]
    public float trackingSmoothing = 0.15f;
    
    [Tooltip("Ignore tiny movements below this threshold")]
    public float deadzone = 0.01f;
    
    [Tooltip("Enable depth (Z) tracking - disable for simpler, more stable effect")]
    public bool useDepthTracking = false;
    
    // UDP
    private UdpClient client;
    private Thread receiveThread;
    private volatile bool isRunning = false;
    private readonly object lockObject = new object();
    
    // Thread-safe eye position storage
    private float _eyeX, _eyeY, _eyeZ;
    private bool hasNewData = false;
    
    // Camera frustum
    private Camera cam;
    private Vector3 targetPosition;
    private Vector3 basePosition;
    
    [Header("Build Performance Settings")]
    [Tooltip("Target framerate (60 recommended, -1 for unlimited)")]
    public int targetFrameRate = 60;
    
    [Tooltip("Quality level (0=Fastest, 5=Fantastic). Set lower for better performance.")]
    [Range(0, 5)]
    public int qualityLevel = 5;
    
    [Tooltip("Fixed resolution width (0 = use native resolution)")]
    public int fixedWidth = 1920;
    
    [Tooltip("Fixed resolution height (0 = use native resolution)")]
    public int fixedHeight = 1080;
    
    [Tooltip("Fullscreen mode")]
    public bool fullscreen = false;
    
    [Tooltip("Enable VSync (can cause input lag)")]
    public bool useVSync = false;

    void Start()
    {
        // Apply performance settings FIRST
        ApplyPerformanceSettings();

        cam = GetComponent<Camera>();
        CalculateOptimalScales();
        
        // Store initial position
        basePosition = transform.position;
        targetPosition = transform.position;
        
        // Start UDP receiver
        StartUDPReceiver();
        
        Debug.Log($"Geometric Parallax Camera Started");
        Debug.Log($"Horizontal Scale: {horizontalScale:F3}, Vertical Scale: {verticalScale:F3}, Depth Scale: {depthScale:F3}");
    }
    
    void ApplyPerformanceSettings()
    {
        // Clear any cached PlayerPrefs that might affect resolution
        PlayerPrefs.DeleteKey("Screenmanager Resolution Width");
        PlayerPrefs.DeleteKey("Screenmanager Resolution Height");
        PlayerPrefs.DeleteKey("Screenmanager Fullscreen mode");
        PlayerPrefs.DeleteKey("UnityGraphicsQuality");
        PlayerPrefs.Save();
        
        // Set target framerate
        Application.targetFrameRate = targetFrameRate;
        
        // Set VSync (0 = off, 1 = on)
        QualitySettings.vSyncCount = useVSync ? 1 : 0;
        
        // Set quality level
        QualitySettings.SetQualityLevel(qualityLevel, true);
        
        // Apply resolution scaling (only in builds, not editor)
        #if !UNITY_EDITOR
        int width = fixedWidth > 0 ? fixedWidth : Screen.currentResolution.width;
        int height = fixedHeight > 0 ? fixedHeight : Screen.currentResolution.height;
        FullScreenMode mode = fullscreen ? FullScreenMode.FullScreenWindow : FullScreenMode.Windowed;
        Screen.SetResolution(width, height, mode);
        Debug.Log($"Resolution FORCED to {width}x{height}, Fullscreen={fullscreen}");
        #endif
        
        Debug.Log($"Performance: Quality={qualityLevel}, FPS={targetFrameRate}, VSync={useVSync}");
    }

    void StartUDPReceiver()
    {
        try
        {
            client = new UdpClient();
            client.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
            client.Client.Bind(new IPEndPoint(IPAddress.Any, port));
            client.Client.ReceiveTimeout = 100; // 100ms timeout - prevents blocking forever
            
            isRunning = true;
            receiveThread = new Thread(new ThreadStart(ReceiveData));
            receiveThread.IsBackground = true;
            receiveThread.Start();
            
            Debug.Log($"UDP Receiver started on port {port}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to start UDP receiver: {e.Message}");
        }
    }
    
    void CalculateOptimalScales()
    {
        // Calculate the ratio between virtual world and physical screen
        horizontalScale = virtualWorldWidth / screenWidth;
        verticalScale = virtualWorldHeight / screenHeight;
        
        // Depth scale: how much virtual depth per meter of real depth
        depthScale = virtualWorldDepth / viewingDistance;
        
        Debug.Log($"Screen: {screenWidth}m x {screenHeight}m at {viewingDistance}m distance");
        Debug.Log($"Virtual World: {virtualWorldWidth} x {virtualWorldHeight} x {virtualWorldDepth} units");
    }
    
    void Update()
    {
        // Get latest tracking data thread-safely
        float currentEyeX, currentEyeY, currentEyeZ;
        lock (lockObject)
        {
            currentEyeX = _eyeX;
            currentEyeY = _eyeY;
            currentEyeZ = _eyeZ;
        }
        
        // Smooth the incoming eye tracking data to reduce jitter
        smoothedX = Mathf.Lerp(smoothedX, currentEyeX, trackingSmoothing);
        smoothedY = Mathf.Lerp(smoothedY, currentEyeY, trackingSmoothing);
        smoothedZ = Mathf.Lerp(smoothedZ, currentEyeZ, trackingSmoothing);
        
        // Apply deadzone to ignore micro-movements
        float filteredX = Mathf.Abs(smoothedX) > deadzone ? smoothedX : 0f;
        float filteredY = Mathf.Abs(smoothedY) > deadzone ? smoothedY : 0f;
        float filteredZ = Mathf.Abs(smoothedZ) > deadzone ? smoothedZ : 0f;
        
        // Calculate head position in physical space (meters)
        float headX_meters = filteredX * (screenWidth / 2f);
        float headY_meters = filteredY * (screenHeight / 2f);
        
        // Viewing distance - either fixed or dynamic based on Z tracking
        float actualDistance;
        if (useDepthTracking)
        {
            // Z represents forward/backward movement from typical viewing distance
            float headZ_meters = filteredZ * 0.3f; // ±0.3m max movement (increased range)
            actualDistance = viewingDistance - headZ_meters; // Subtract: leaning forward = closer = smaller distance
            actualDistance = Mathf.Clamp(actualDistance, 0.25f, 1.5f);
        }
        else
        {
            // Fixed viewing distance - simpler and more stable
            actualDistance = viewingDistance;
        }
        
        // HEAD-COUPLED PERSPECTIVE: Calculate off-center frustum
        // This creates the "looking through a window" effect
        float near = cam.nearClipPlane;
        float far = cam.farClipPlane;
        
        // Calculate frustum bounds at the near plane based on head position
        // The screen acts as a window, and we adjust what's visible based on viewing angle
        float frustumHeight = 2f * near * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        float frustumWidth = frustumHeight * cam.aspect;
        
        // Map physical screen position to near plane
        // The key insight: as head moves, the viewing frustum shifts asymmetrically
        float screenToNearRatio = near / actualDistance;
        
        float xOffset = headX_meters * screenToNearRatio * parallaxIntensity;
        float yOffset = headY_meters * screenToNearRatio * parallaxIntensity;
        
        // Calculate asymmetric frustum bounds
        float left = -frustumWidth * 0.5f + xOffset;
        float right = frustumWidth * 0.5f + xOffset;
        float bottom = -frustumHeight * 0.5f + yOffset;
        float top = frustumHeight * 0.5f + yOffset;
        
        // Build the off-center projection matrix
        Matrix4x4 projectionMatrix = Matrix4x4.Frustum(left, right, bottom, top, near, far);
        cam.projectionMatrix = projectionMatrix;
        
        // Debug
        if (Time.frameCount % 60 == 0)
        {
            Debug.Log($"Head: X:{headX_meters:F3}m, Y:{headY_meters:F3}m, Z:{actualDistance:F3}m | Frustum: L:{left:F2}, R:{right:F2}, B:{bottom:F2}, T:{top:F2}");
        }
    }
    
    void OnDisable()
    {
        // Reset projection matrix when disabled
        if (cam != null)
        {
            cam.ResetProjectionMatrix();
        }
    }
    
    void ReceiveData()
    {
        byte[] data = new byte[12];
        EndPoint remoteEP = new IPEndPoint(IPAddress.Any, 0);
        
        while (isRunning)
        {
            try
            {
                // Use ReceiveFrom with timeout - won't block forever
                int received = client.Client.ReceiveFrom(data, ref remoteEP);
                
                if (received == 12) // 3 floats * 4 bytes
                {
                    float x = BitConverter.ToSingle(data, 0);
                    float y = BitConverter.ToSingle(data, 4);
                    float z = BitConverter.ToSingle(data, 8);
                    
                    // Thread-safe update
                    lock (lockObject)
                    {
                        _eyeX = x;
                        _eyeY = y;
                        _eyeZ = z;
                        hasNewData = true;
                    }
                }
            }
            catch (SocketException e)
            {
                // Timeout is expected (error code 10060), just continue
                if (e.SocketErrorCode != SocketError.TimedOut)
                {
                    Debug.LogWarning($"Socket error: {e.SocketErrorCode}");
                }
            }
            catch (Exception e)
            {
                if (isRunning) // Only log if we're still supposed to be running
                {
                    Debug.LogWarning($"UDP receive error: {e.Message}");
                }
            }
        }
        
        Debug.Log("UDP receiver thread ended");
    }
    
    void OnApplicationQuit()
    {
        CleanupUDP();
    }
    
    void OnDestroy()
    {
        CleanupUDP();
    }
    
    void CleanupUDP()
    {
        isRunning = false;
        
        // Close the socket first - this will unblock any waiting Receive calls
        if (client != null)
        {
            try
            {
                client.Close();
            }
            catch { }
            client = null;
        }
        
        // Now wait for thread to finish (with timeout)
        if (receiveThread != null && receiveThread.IsAlive)
        {
            if (!receiveThread.Join(500)) // Wait max 500ms
            {
                Debug.LogWarning("UDP thread did not terminate in time");
            }
            receiveThread = null;
        }
    }
}