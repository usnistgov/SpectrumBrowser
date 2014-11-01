package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;


public class AdminServiceImpl extends AbstractSpectrumBrowserService implements AdminService {

	public AdminServiceImpl(String baseurl) {
		super.baseUrl = baseurl;
	}
    
	@Override
	public void getAdminBand(String sessionId, String bandName,
			SpectrumBrowserCallback<String> callback) {
		String uri = "getAdminBand/" + sessionId + "/" + bandName;
		dispatch(uri, callback);
	}
}
