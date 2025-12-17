#!/bin/sh
# /etc/config/wireless snippet for OpenWRT

# Enable 802.11s Mesh
uci set wireless.radio0.channel='13' # Non-overlapping
uci set wireless.default_radio0.mode='mesh'
uci set wireless.default_radio0.mesh_id='EDGE_LATTICE_01'
uci set wireless.default_radio0.encryption='sae'
uci set wireless.default_radio0.key='SuperSecureSecretKey' # SAE Password
uci set wireless.default_radio0.mesh_fwding='1'

uci commit wireless
wifi reload

# Install TWAMP for telemetry
opkg update
opkg install twamp-light

