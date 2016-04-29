package gov.nist.spectrumbrowser.admin;

import java.util.logging.Logger;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;


public class AdminServiceImpl extends AbstractSpectrumBrowserService implements AdminService {
	private static final Logger logger = Logger.getLogger("SpectrumBrowser");

	public AdminServiceImpl(String baseurl) {
		logger.finer("AdminService " + baseurl);
		super.baseUrl = baseurl;
	}

	@Override
	public void authenticate(String jsonContent, SpectrumBrowserCallback<String> callback){
		super.dispatchWithJsonContent("authenticate", jsonContent, callback);
	}

	@Override
	public void logOut(SpectrumBrowserCallback<String> callback) {
		String sessionToken = Admin.getSessionToken();
		Admin.clearSessionTokens();
		super.dispatch("logOut/" + sessionToken, callback);	
	}

	@Override
	public void getSystemConfig(SpectrumBrowserCallback<String> callback) {
		String uri = "getSystemConfig/"+ Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void setSystemConfig(String jsonContent, SpectrumBrowserCallback<String> callback) {
		String uri = "setSystemConfig/" + Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, jsonContent, callback);
	}


	@Override
	public void getPeers(SpectrumBrowserCallback<String> callback) {
		String uri = "getPeers/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}
	
	@Override
	public void getUserAccounts(SpectrumBrowserCallback<String> callback) {
		String uri = "getUserAccounts/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}
	
	@Override
	public void addAccount(String jsonContent, SpectrumBrowserCallback<String> callback) {
		String uri = "createAccount/" + Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, jsonContent, callback);
	}
	
	
	@Override
	public void deleteAccount(String emailAddress, SpectrumBrowserCallback<String> callback) {
		String uri = "deleteAccount/" + emailAddress + "/" + Admin.getSessionToken();
		logger.finer("email to delete Account " + emailAddress);
		super.dispatch(uri, callback);
	}
	
	@Override
	public void togglePrivilegeAccount(String emailAddress, SpectrumBrowserCallback<String> callback) {
		String uri = "togglePrivilegeAccount/" + emailAddress + "/" + Admin.getSessionToken();
		logger.finer("email to delete Account " + emailAddress);
		super.dispatch(uri, callback);
	}
	
	@Override
	public void unlockAccount(String emailAddress, SpectrumBrowserCallback<String> callback) {
		String uri = "unlockAccount/" + emailAddress + "/" + Admin.getSessionToken();
		logger.finer("email to unlock Account " + emailAddress);
		super.dispatch(uri, callback);
	}
	
	@Override
	public void resetAccountExpiration(String emailAddress, SpectrumBrowserCallback<String> callback) {
		String uri = "resetAccountExpiration/" + emailAddress + "/" + Admin.getSessionToken();
		logger.finer("email to reset Account expiration " + emailAddress);
		super.dispatch(uri, callback);
	}
	
	@Override
	public void removePeer(String host, int port, SpectrumBrowserCallback<String> callback) {
		String uri = "removePeer/" + host + "/" + port + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void addPeer(String host, int port, String protocol,
			SpectrumBrowserCallback<String> callback) {
		String uri = "addPeer/" + host + "/" + port + "/" + protocol + "/"  + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void getInboundPeers(SpectrumBrowserCallback<String> callback) {
		String uri = "getInboundPeers/" + Admin.getSessionToken();
		super.dispatch(uri,callback);
	}

	@Override
	public void deleteInboundPeer(String peerId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "deleteInboundPeer/" + peerId + "/"	+ Admin.getSessionToken();	
		super.dispatch(uri, callback);
	}

	@Override
	public void addInboundPeer(String data, SpectrumBrowserCallback<String> callback) {
		String uri = "addInboundPeer/"+Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, data, callback);
	}

	@Override
	public void getSensorInfo(boolean getFirstLastMessages, SpectrumBrowserCallback<String> callback) {
		String uri = "getSensorInfo/" + Admin.getSessionToken() + "?" + "getFirstLastMessages=" + getFirstLastMessages;
		super.dispatch(uri, callback);
	}

	@Override
	public void addSensor(String sensorInfo,
			SpectrumBrowserCallback<String> callback) {
		String uri = "addSensor/" + Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, sensorInfo, callback);		
	}

	@Override
	public void toggleSensorStatus(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "toggleSensorStatus/" + sensorId + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
		
	}

	@Override
	public void updateSensor(String sensorInfo, 
			SpectrumBrowserCallback<String> callback) {
		String uri = "updateSensor/"+Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, sensorInfo, callback);
	}

	@Override
	public void purgeSensor(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "purgeSensor/" + sensorId + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
		
	}

	@Override
	public void recomputeOccupancies(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "recomputeOccupancies/" + sensorId + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
		
	}

	@Override
	public void garbageCollect(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "garbageCollect/" + sensorId + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void getSystemMessages(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "getSystemMessages/" + sensorId + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void getSessions(
			SpectrumBrowserCallback<String> callback) {
		String uri = "getSessions/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void freezeSessions(SpectrumBrowserCallback<String> callback) {
		String uri = "freezeRequest/" + Admin.getSessionToken();
		super.dispatch(uri,callback);
		
	}
	
	@Override
	public void unfreezeSessions(SpectrumBrowserCallback<String> callback) {
		String uri = "unfreezeRequest/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void setScreenConfig(String jsonContent, SpectrumBrowserCallback<String> callback) {
		String uri = "setScreenConfig/" + Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, jsonContent, callback);
	}

	@Override
	public void getScreenConfig(SpectrumBrowserCallback<String> callback) {
		String uri = "getScreenConfig/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void getServiceStatus(String service, SpectrumBrowserCallback<String> callback) {
		if ( Admin.getSessionToken() != null) {
			String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";
			String uri = "getServiceStatus/" + service + "/" + Admin.getSessionToken();
			super.dispatch(baseUrl,uri, callback);
		}
	}

	@Override
	public void stopService(String service, SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";
		String uri = "stopService/" + service + "/" + Admin.getSessionToken();
		super.dispatch(baseUrl,uri, callback);
	}
	
	@Override
	public void restartService(String service, SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";
		String uri = "restartService/" + service + "/" + Admin.getSessionToken();
		super.dispatch(baseUrl,uri, callback);
	}

	@Override
	public void getServicesStatus(SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";
		String uri = "getServicesStatus/"+ Admin.getSessionToken();
		super.dispatch(baseUrl,uri, callback);
	}

	@Override
	public void getESAgents(SpectrumBrowserCallback<String> callback) {
		String uri = "getESAgents/"+ Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void addEsAgent(String requestData,
			SpectrumBrowserCallback<String> callback) {
		String uri = "addESAgent/"+ Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, requestData, callback);
	}

	@Override
	public void deleteESAgent(String agentName,
			SpectrumBrowserCallback<String> callback) {
		String uri = "deleteESAgent/"+agentName + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void getDebugFlags(SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";

		String uri = "getDebugFlags/" + Admin.getSessionToken();
		super.dispatch(baseUrl, uri, callback);
		
	}
	
	@Override
	public void setDebugFlags(String requestData,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";
		String uri = "setDebugFlags/" + Admin.getSessionToken();
		super.dispatchWithJsonContent(baseUrl, uri, requestData, callback);
		
	}

	@Override
	public void getLogs(SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";

		String uri = "getLogs/" + Admin.getSessionToken();
		super.dispatch(baseUrl, uri, callback);
	}
	
	@Override
	public void clearLogs(SpectrumBrowserCallback<String> callback) {
		String baseUrl = Admin.getBaseUrlAuthority() + "/svc/";

		String uri = "clearLogs/" + Admin.getSessionToken();
		super.dispatch(baseUrl, uri, callback);
	}

	
	@Override
	public void verifySessionToken(SpectrumBrowserCallback<String> callback) {
		String uri = "verifySessionToken/" + Admin.getSessionToken();
		super.dispatch(uri,callback);
		
	}
	
	@Override
	public void changePassword(String jsonContent, SpectrumBrowserCallback<String> callback) {
		String url = "changePassword";
		dispatchWithJsonContent(url, jsonContent, callback);
	}
    
	
}
