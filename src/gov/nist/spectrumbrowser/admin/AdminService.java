/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
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

	public void getSensorInfo(boolean getMessageDates, SpectrumBrowserCallback<String> callback);

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

	public void getESAgents(SpectrumBrowserCallback<String>  callback);

	public void addEsAgent(String string, SpectrumBrowserCallback<String> callback);

	public void deleteESAgent(String agentName, SpectrumBrowserCallback<String> callback);

	public void getDebugFlags(SpectrumBrowserCallback<String> callback);
	
	public void setDebugFlags(String flags, SpectrumBrowserCallback<String> callback);

	public void getLogs(SpectrumBrowserCallback<String> callback);

	public void clearLogs(SpectrumBrowserCallback<String> callback);

	public void verifySessionToken( SpectrumBrowserCallback<String> callback);

	void changePassword(String accountInfo, SpectrumBrowserCallback<String> callback);

	public void armSensor(String sensorId, boolean armFlag, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void deleteAllCaptureEvents(String sensorId, SpectrumBrowserCallback<String> spectrumBrowserCallback);
	

}
