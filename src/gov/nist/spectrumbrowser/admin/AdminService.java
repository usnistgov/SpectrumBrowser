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
	public void logOut(String sessionId, SpectrumBrowserCallback<String> callback);

	/**
	 * Gets the location names for which data is available.
	 * 
	 * @param sessionId - session id returned by authentication
	 * @return a json string containing the location names.
	 * @throws IllegalArgumentException
	 */
	void getAdminBand(String sessionId, String bandName, SpectrumBrowserCallback<String> SpectrumBrowserCallback)throws IllegalArgumentException;
}
