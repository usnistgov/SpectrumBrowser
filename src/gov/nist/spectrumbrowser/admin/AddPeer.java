package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class AddPeer {
	
	private VerticalPanel verticalPanel;
	private Peers peers;
	private Admin admin;

	public AddPeer(Admin admin, Peers peers, VerticalPanel verticalPanel) {
		this.verticalPanel = verticalPanel;
		this.peers = peers;
		this.admin = admin;
	}
	
	private boolean validateHost(String ip) {
		try {
	        if (ip == null || ip.isEmpty()) {
	            return false;
	        }

	        String[] parts = ip.split( "\\." );
	        if ( parts.length != 4 ) {
	            return false;
	        }

	        for ( String s : parts ) {
	            int i = Integer.parseInt( s );
	            if ( (i < 0) || (i > 255) ) {
	                return false;
	            }
	        }
	        if(ip.endsWith(".")) {
	            return false;
	        }
	        return true;
	    } catch (NumberFormatException nfe) {
            return false;
	    }
	}
	
	private boolean validatePort(String portStr) {

		try {
			int port = Integer.parseInt(portStr);
			if ( port < 0 ) {
				return false;
			}
			return true;
		} catch (NumberFormatException nfe) {
			return false;
		}
	}

	public void draw() {		
		verticalPanel.clear();
		HTML html = new HTML("<H2>Add peer for outbound registration</H2>");
		verticalPanel.add(html);
		Grid grid = new Grid(3,2);
		grid.setText(0, 0, "Host");
		verticalPanel.add(grid);
		
		final TextBox nameTextBox = new TextBox();
		grid.setWidget(0, 1, nameTextBox);
		nameTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String ip = event.getValue();
				if (!validateHost(ip)) {
					Window.alert("Please enter a valid IP address");
					nameTextBox.setText("");
				}
			}});
		
		
		grid.setText(1, 0, "Port");
		final TextBox portTextBox = new TextBox();
		portTextBox.setText("443");
		portTextBox.addValueChangeHandler(new ValueChangeHandler<String> (){

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String portStr = event.getValue();
				if (! validatePort(portStr)) {
					Window.alert("Please enter valid port");
					portTextBox.setText("443");
				}
				
			}});
		grid.setWidget(1, 1, portTextBox);

		grid.setText(2, 0, "Protocol");
		final TextBox protocolTextBox = new TextBox();
		protocolTextBox.setText("https");
		protocolTextBox.addValueChangeHandler(new ValueChangeHandler<String>(){

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String protocol = event.getValue();
				if (!protocol.equals("http") && !protocol.equals("http")){
					Window.alert("please enter http or https");
					protocolTextBox.setText("https");
				}
			}});
		grid.setWidget(2, 1, protocolTextBox);
		
		
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		
		
		Button applyButton = new Button("Add");
		applyButton.addClickHandler(new ClickHandler(){

			@Override
			public void onClick(ClickEvent event) {
				String host = nameTextBox.getValue();
				if ( ! validateHost(host)) {
					Window.alert("Please enter valid host name");
					return;
				}
				int port = Integer.parseInt(portTextBox.getText());
				if (! validatePort(portTextBox.getText()) ) {
					Window.alert("please enter valid port");
					return;
				}
				String protocol = protocolTextBox.getText();
				Admin.getAdminService().addPeer(host,port,protocol,peers);
			}});
		horizontalPanel.add(applyButton);

	
		Button cancelButton = new Button("Cancel");
		horizontalPanel.add(cancelButton);
		cancelButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				peers.draw();
			}});
		
		Button logoffButton = new Button("Log Off");
		horizontalPanel.add(logoffButton);
		logoffButton.addClickHandler( new ClickHandler(){

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
				return;
			}});
		
		
		verticalPanel.add(horizontalPanel);
		

	}

}
