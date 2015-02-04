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
	public void authenticate(String userName, 
			String password, String privilege, SpectrumBrowserCallback<String> callback){
		super.dispatch("authenticate/" + privilege + "/" + userName + "?password="+password, callback);
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
	public void removePeer(String host, int port, SpectrumBrowserCallback<String> callback) {
		String uri = "removePeer/" + host + "/" + port + "/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void getAdminBand(String bandName,
			SpectrumBrowserCallback<String> callback) {
		// TODO Auto-generated method stub
		
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
	public void getSensorInfo(SpectrumBrowserCallback<String> callback) {
		String uri = "getSensorInfo/" + Admin.getSessionToken();
		super.dispatch(uri, callback);
	}

	@Override
	public void addSensor(String sensorInfo,
			SpectrumBrowserCallback<String> callback) {
		String uri = "addSensor/" + Admin.getSessionToken();
		super.dispatchWithJsonContent(uri, sensorInfo, callback);		
	}

	@Override
	public void removeSensor(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String uri = "removeSensor/" + sensorId + "/" + Admin.getSessionToken();
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
    
	
}
