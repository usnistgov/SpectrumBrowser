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
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.logical.shared.SelectionEvent;
import com.google.gwt.event.logical.shared.SelectionHandler;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.TabPanel;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * 
 * @author local
 *
 */
class AdminScreen implements SpectrumBrowserCallback<String> {

	private VerticalPanel verticalPanel;
	private Admin adminEntryPoint;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private TabPanel tabPanel;
	private SpectrumBrowserScreen[] screens = new SpectrumBrowserScreen[7];
	private SessionManagement sessionManagement;

	public AdminScreen(VerticalPanel verticalPanel, Admin adminEntryPoint) {
		logger.finer("AdminScreen");
		this.verticalPanel = verticalPanel;
		this.adminEntryPoint = adminEntryPoint;
	}

	public void draw() {
		try {

			verticalPanel.clear();
			HTML html = new HTML(
					"<h2>CAC Measured Spectrum Occupancy Database Administrator Interface</h> ",
					true);
			verticalPanel.add(html);

			tabPanel = new TabPanel();

			int counter = 0;
			
			SystemConfig systemConfig = new SystemConfig(adminEntryPoint);
			screens[counter++] = systemConfig;
			tabPanel.add(systemConfig, systemConfig.getEndLabel());
			ScreenConfig screenConfig = new ScreenConfig(adminEntryPoint);
			screens[counter++] = screenConfig;
			tabPanel.add(screenConfig,screenConfig.getEndLabel());
			OutboundPeers peers = new OutboundPeers(adminEntryPoint);
			screens[counter++] = peers;
			tabPanel.add(peers,peers.getEndLabel());
			InboundPeers inboundPeers = new InboundPeers(adminEntryPoint);
			screens[counter++] = inboundPeers;
			tabPanel.add(inboundPeers,inboundPeers.getEndLabel());
			SensorConfig sensorConfig = new SensorConfig(adminEntryPoint);
			screens[counter++] = sensorConfig;
			tabPanel.add(sensorConfig,sensorConfig.getEndLabel());
			AccountManagement accountMgmt = new AccountManagement(adminEntryPoint);
			screens[counter++] = accountMgmt;
			tabPanel.add(accountMgmt, accountMgmt.getEndLabel()); 
			SessionManagement sessionManagement = new SessionManagement(adminEntryPoint);
			ESAgents esAgents = new ESAgents(adminEntryPoint);
			screens[counter++] = esAgents;
			tabPanel.add(esAgents,esAgents.getEndLabel());
			screens[counter++] = sessionManagement;
			this.sessionManagement = sessionManagement;
			tabPanel.add(sessionManagement,sessionManagement.getEndLabel());
			SystemMonitor monitor = new SystemMonitor(adminEntryPoint);
			screens[counter++] = monitor;
			tabPanel.add(monitor,monitor.getEndLabel());
			DebugConfiguration debugConfig = new DebugConfiguration(adminEntryPoint);
			screens[counter++] = debugConfig;
			tabPanel.add(debugConfig,debugConfig.getEndLabel());
			ServiceControl serviceControl = new ServiceControl(adminEntryPoint);
			screens[counter++] = serviceControl;
			tabPanel.add(serviceControl,serviceControl.getEndLabel());
			
			tabPanel.addSelectionHandler(new SelectionHandler<Integer>() {

				@Override
				public void onSelection(SelectionEvent<Integer> event) {
					int selection = event.getSelectedItem();
					screens[selection].draw();
				}
			});
			
			verticalPanel.add(tabPanel);
			
			Timer timer = new Timer() {

				@Override
				public void run() {
					tabPanel.selectTab(0);
				}  };

			timer.schedule(1000);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem drawing Admin Screen", th);
			adminEntryPoint.logoff();
		}

	}

	@Override
	public void onSuccess(String result) {}

	@Override
	public void onFailure(Throwable throwable) {}

	public void cancelTimers() {
		sessionManagement.cancelTimer();
	}

}
