package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

public interface AdminService {
	

	
	/**
	 * Authenticate the administrator.
	 * @param userName
	 * @param password
	 * @param callback
	 */
	public void authenticate(String jsonContent, SpectrumBrowserCallback<String> callback);

	/**
	 * Log off from admin 
	 * @param sessionId
	 * @param callback
	 */
	public void logOut(SpectrumBrowserCallback<String> callback);
	
	/**
	 * get the System configuration json object.
	 * 
	 * @param callback
	 */
	public void getSystemConfig(SpectrumBrowserCallback<String> callback);
	
	public void getPeers(SpectrumBrowserCallback<String> callback);

	void setSystemConfig(String jsonContent, SpectrumBrowserCallback<String> callback);

	public void removePeer(String host, int port, SpectrumBrowserCallback<String> callback);

	public void addPeer(String host, int port, String protocol, SpectrumBrowserCallback<String> callback);
	
	public void getInboundPeers(SpectrumBrowserCallback<String> callback);
	
	public void getUserAccounts(SpectrumBrowserCallback<String> callback);
	
	public void addAccount(String jsonContent, SpectrumBrowserCallback<String> callback);
	
	public void deleteAccount(String emailAddress, SpectrumBrowserCallback<String> callback);
	
	public void togglePrivilegeAccount(String emailAddress, SpectrumBrowserCallback<String> callback);
	
	public void unlockAccount(String emailAddress, SpectrumBrowserCallback<String> callback);
	
	public void resetAccountExpiration(String emailAddress, SpectrumBrowserCallback<String> callback);

	public void deleteInboundPeer(String peerId, SpectrumBrowserCallback<String> callback);

	public void addInboundPeer(String string, SpectrumBrowserCallback<String> callback);

	public void getSensorInfo(SpectrumBrowserCallback<String> callback);

	public void addSensor(String sensorInfo, SpectrumBrowserCallback<String> callback);

	public void toggleSensorStatus(String sensorId, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void updateSensor(String sensorInfo, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void purgeSensor(String sensorId, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void recomputeOccupancies(String sensorId, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void garbageCollect(String sensorId, SpectrumBrowserCallback<String> callback);

	public void getSystemMessages(String sensorId, SpectrumBrowserCallback<String> callback);

	public void getSessions(SpectrumBrowserCallback<String> spectrumBrowserCallback);
	
	public void freezeSessions(SpectrumBrowserCallback<String> callback);
	
	public void unfreezeSessions(SpectrumBrowserCallback<String> callback);
	
	void setScreenConfig(String jsonContent, SpectrumBrowserCallback<String> callback);
	
	public void getScreenConfig(SpectrumBrowserCallback<String> callback);

	public void getServiceStatus(String service, SpectrumBrowserCallback<String> callback);

	public void stopService(String service, SpectrumBrowserCallback<String> spectrumBrowserCallback);
	
	public void restartService(String service, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void getServicesStatus(SpectrumBrowserCallback<String> callback);

	

}
