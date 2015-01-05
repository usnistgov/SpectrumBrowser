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
		super.dispatch("authenticate/" + userName + "/" + privilege + "?password="+password, callback);
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
	public void getStreamingConfig(SpectrumBrowserCallback<String> callback) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void setStreamingConfig(int streamingSampleInterval,
			int streamingCaptureSize, int streamingSecondsPerFrame,
			String streamingFilter, int streamingBasePort,
			SpectrumBrowserCallback<String> callback) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void getPeers(SpectrumBrowserCallback<String> callback) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void getAdminBand(String bandName,
			SpectrumBrowserCallback<String> callback) {
		// TODO Auto-generated method stub
		
	}
    
	
}
