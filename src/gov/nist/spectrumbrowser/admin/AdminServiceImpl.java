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
			String password, String browserPage, SpectrumBrowserCallback<String> callback){
		super.dispatch("authenticate/" + browserPage + "/" + userName + "?password="+password, callback);
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
    
	
}
