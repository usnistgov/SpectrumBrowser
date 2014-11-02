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
	public void getAdminBand(String sessionId, String bandName,
			SpectrumBrowserCallback<String> callback) {
		String uri = "getAdminBand/" + sessionId + "/" + bandName;
		dispatch(uri, callback);
	}
}
