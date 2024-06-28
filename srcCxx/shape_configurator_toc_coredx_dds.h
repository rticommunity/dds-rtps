
#include <dds/dds.hh>
#include "shape.hh"
#include "shapeTypeSupport.hh"
#include "shapeDataReader.hh"
#include "shapeDataWriter.hh"

#define CONFIGURE_PARTICIPANT_FACTORY config_transport();
#define LISTENER_STATUS_MASK_ALL (ALL_STATUS)

void StringSeq_push(DDS::StringSeq  &string_seq, const char *elem)
{
  string_seq.push_back((char*)elem);
}

const char *get_qos_policy_name(DDS_QosPolicyId_t policy_id)
{
  return DDS_qos_policy_str(policy_id); // not standard...
}



static void config_transport()
{
  setenv( "COREDX_UDP_RX_BUFFER_SIZE", "65536", 1 ); /* so we don't miss the first packets if they are large, retransmits may throw off test timing */
}
