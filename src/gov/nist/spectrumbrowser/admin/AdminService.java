package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

public interface AdminService {
	

	
	/**
	 * Authenticate the administrator.
	 * @param userName
	 * @param password
	 * @param callback
	 */
	public void authenticate(String userName, String password, String privilege, SpectrumBrowserCallback<String> callback);

	/**
	 * Log off from admin 
	 * @param sessionId
	 * @param callback
	 */
	public void logOut(SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId
	 * @param callback
	 */
	public void getSystemConfig(SpectrumBrowserCallback<String> callback);
	
		
	public void getPeers(SpectrumBrowserCallback<String> callback);
	
	public void getAdminBand(String bandName, SpectrumBrowserCallback<String> callback);

	void setSystemConfig(String jsonContent,
			SpectrumBrowserCallback<String> callback);

	public void removePeer(String host, int port, SpectrumBrowserCallback<String> callback);

	public void addPeer(String host, int port, String protocol, SpectrumBrowserCallback<String> callback);
	
	public void getInboundPeers(SpectrumBrowserCallback<String> callback);

	public void deleteInboundPeer(String peerId, SpectrumBrowserCallback<String> callback);

	public void addInboundPeer(String string, SpectrumBrowserCallback<String> callback);

	public void getSensorInfo(SpectrumBrowserCallback<String> callback);

	public void addSensor(String sensorInfo, SpectrumBrowserCallback<String> callback);

	public void removeSensor(String sensorId, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void updateSensor(String sensorInfo,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void purgeSensor(String sensorId,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);

}
